import ast
import ctypes
import llvmlite.ir as ir
import llvmlite.binding as llvm
import base64

from dataclasses import dataclass, field

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

ir_ptr_t = ir.PointerType
ir_int32_t = ir.IntType(32)
ir_int64_t = ir.IntType(64)
ir_int128_t = ir.IntType(128)
ir_float_t = ir.FloatType()
ir_double_t = ir.DoubleType()
ir_bool_t = ir.IntType(64)
ir_void_t = ir.VoidType()
ir_void_ptr_t = ir_ptr_t(ir.IntType(8))

py_int = type(1)
py_float = type(1.0)

pytype2irtype = {
    py_int: ir_int64_t,
    py_float: ir_double_t
}

@dataclass
class FunctionCtx:
    name: str
    locals: dict = field(default_factory=dict)
    irbuilder: ir.IRBuilder = None
    retval: ir.instructions.AllocaInstr = None
    ir_func: ir.Function = None
    ir_entry_block: ir.Block = None
    ir_exit_block: ir.Block = None

class ASTVisitor(ast.NodeVisitor):

    def __init__(self):
        self.functions = {}
        self.is_inside_function = False
        self.current_function = None
        self.is_inside_class = False
        self.module = None
        self.should_load_stack = []
        self.globals = {}

    def __call__(self, node):
        assert isinstance(node, ast.Module)
        self.visit(node)
        return self.module

    def add_global_variable(self, name, val):
        irconst = self.visit_Constant(val)
        gvar = ir.GlobalVariable(self.module, irconst.type, name)
        gvar.initializer = irconst
    
    def get_global_variable(self, name):
        return self.module.globals.get(name)

    def add_local_variable(self, name, ty):
        self.current_function.locals[name] = \
            self.current_function.irbuilder.alloca(ty, name=name)
        
    def get_or_add_local_variable(self, name, ty):
        if name in self.current_function.locals:
            return self.current_function.locals[name]
        else:
            self.add_local_variable(name, ty)
            return self.current_function.locals[name]

    def get_variable(self, name):
        maybe_gvar = self.get_global_variable(name)
        if maybe_gvar:
            loaded_gvar = self.current_function.irbuilder.load(maybe_gvar)
            return loaded_gvar
        maybe_lvar = self.current_function.locals.get(name)
        if maybe_lvar:
            loaded_lvar = self.current_function.irbuilder.load(maybe_lvar)
            return loaded_lvar
        raise NameError(f"Variable {name} not found")
    
    def get_array_variable(self, name):
        maybe_lvar = self.current_function.locals.get(name)
        assert maybe_lvar
        return maybe_lvar
        
    def visit_Constant(self, node):
        ty = pytype2irtype[type(node.value)]
        return ir.Constant(ty, node.value)

    def visit_Module(self, node):
        assert len(node.body) == 1
        assert isinstance(node.body[0], ast.ClassDef)
        self.visit(node.body[0])

    def visit_ClassDef(self, node):
        assert not self.is_inside_function
        assert not self.is_inside_class
        assert self.module is None
        self.is_inside_class = True
        self.module = ir.Module(name=node.name)
        for stmt in node.body:
            assert isinstance(stmt, ast.FunctionDef) or isinstance(stmt, ast.Assign)
            match stmt:
                case ast.FunctionDef():
                    self.visit_FunctionDef(stmt)
                case ast.Assign():
                    self.visit_Assign(stmt)
                case _:
                    raise NotImplementedError
        self.is_inside_class = False

    def visit_Assign(self, node):
        target = node.targets[0]
        value = node.value
        if isinstance(target, ast.Name):
            match self.is_inside_function, value:
                case False, ast.Constant():
                    self.add_global_variable(target.id, value)
                case True, _:
                    value = self.visit(value, should_load=True)
                    if isinstance(value, ir.instructions.AllocaInstr):
                        assert self.current_function.locals.get(target.id) is None
                        assert self.get_global_variable(target.id) is None
                        self.current_function.locals[target.id] = value
                    else:
                        maybe_gvar = self.get_global_variable(target.id)
                        if maybe_gvar:
                            self.current_function.irbuilder.store(value, maybe_gvar)
                        else:
                            ptr = self.get_or_add_local_variable(target.id, value.type)
                            self.current_function.irbuilder.store(value, ptr)
                case _:
                    raise NotImplementedError
        elif isinstance(target, ast.Subscript):
            assert self.is_inside_function
            ptr = self.visit(target, should_load=False)
            value = self.visit(value, should_load=True)
            self.current_function.irbuilder.store(value, ptr)
        else:
            raise NotImplementedError
            
    def start_function(self, node):
        func_name = node.name
        if func_name == 'main':
            assert len(node.args.args) == 1
        ir_func_type = ir.FunctionType(ir_int64_t, [
            ir_int64_t for arg in node.args.args
        ])
        ir_func = ir.Function(
            self.module, ir_func_type, name=func_name
        )
        ir_func_entrypoint_block = ir_func.append_basic_block('entry')
        ir_func_builder = ir.IRBuilder(ir_func_entrypoint_block)
        retval = ir_func_builder.alloca(ir_int64_t, name="retval")
        ir_exit_block = ir_func.append_basic_block('exit')
        self.current_function = FunctionCtx(name=func_name, irbuilder=ir_func_builder, retval=retval, ir_func=ir_func, ir_entry_block=ir_func_entrypoint_block, ir_exit_block=ir_exit_block)
        for i,arg in enumerate(node.args.args):
            ptr = self.get_or_add_local_variable(arg.arg, ir_int64_t)
            value = ir_func.args[i]
            self.current_function.irbuilder.store(value, ptr)

    def end_function(self):
        if not self.current_function.ir_entry_block.is_terminated:
            self.current_function.irbuilder.branch(self.current_function.ir_exit_block)
        self.current_function.irbuilder.position_at_end(self.current_function.ir_exit_block)
        self.current_function.irbuilder.ret(
            self.current_function.irbuilder.load(
                self.current_function.retval
            )
        )

    def visit_FunctionDef(self, node):
        assert not self.is_inside_function
        assert self.is_inside_class
        self.is_inside_function = True

        self.start_function(node)

        for stm in node.body:
            self.visit(stm)

        self.end_function()
        self.is_inside_function = False
        self.functions[self.current_function.name] = self.current_function
        self.current_function = None
    
    def builtins_Alloc(self, node):
        assert len(node.args) == 1
        assert isinstance(node.args[0], ast.Constant)
        size = self.visit(node.args[0])
        ix = self.current_function.irbuilder.alloca(ir_int64_t, size)
        return ix

    def builtins_Abort(self, node):

        ix = self.current_function.irbuilder.store(
            ir.Constant(ir_int64_t, 0x41414141),
            self.current_function.irbuilder.inttoptr(
                ir.Constant(ir_int64_t, 0x4141414141414141),
                ir_ptr_t(ir_int64_t)
            )
        )
        return ix

    def visit_Call(self, node):
        assert self.is_inside_function
        func_name = node.func.id
        if hasattr(self, f"builtins_{func_name}"):
            return getattr(self, f"builtins_{func_name}")(node)
        if func_name in self.functions:
            func_ctx = self.functions[func_name]
            args = [self.visit(arg) for arg in node.args]
            return self.current_function.irbuilder.call(func_ctx.ir_func, args)
        else:
            raise ValueError(f"Function {func_name} not found")

    def visit_Return(self, node):
        assert self.is_inside_function
        toret = self.visit(node.value, should_load=True)
        self.current_function.irbuilder.store(toret, self.current_function.retval)
        self.current_function.irbuilder.branch(self.current_function.ir_exit_block)

    def visit_BinOp(self, node):
        assert self.is_inside_function
        left = self.visit(node.left, should_load=True)
        right = self.visit(node.right, should_load=True)
        if isinstance(node.op, ast.Add):
            return self.current_function.irbuilder.add(left, right, name="addtmp")
        elif isinstance(node.op, ast.Sub):
            return self.current_function.irbuilder.sub(left, right, name="subtmp")
        elif isinstance(node.op, ast.Mult):
            return self.current_function.irbuilder.mul(left, right, name="multmp")
        elif isinstance(node.op, ast.Div):
            return self.current_function.irbuilder.udiv(left, right, name="divtmp")
        else:
            raise NotImplementedError
        
    def visit_Name(self, node):
        assert type(node.ctx) == ast.Load
        return self.get_variable(node.id)

    def emit_check_bounds(self, index, size):
        zero = ir.Constant(index.type, 0)
        check_bounds = self.current_function.irbuilder.append_basic_block("")
        is_ok_block = self.current_function.irbuilder.append_basic_block("")
        not_ok_block = self.current_function.irbuilder.append_basic_block("")
        self.current_function.irbuilder.branch(check_bounds)
        self.current_function.irbuilder.position_at_end(check_bounds)
        is_non_negative = self.current_function.irbuilder.icmp_signed(">=", index, zero, name="check_non_negative")
        is_within_bound = self.current_function.irbuilder.icmp_signed("<", index, size, name="check_within_bound")
        in_bounds = self.current_function.irbuilder.and_(is_non_negative, is_within_bound, name="check_in_bounds")
        self.current_function.irbuilder.cbranch(
            in_bounds,
            is_ok_block,
            not_ok_block
        )
        self.current_function.irbuilder.position_at_end(not_ok_block)
        self.visit_Call(ast.Call(func=ast.Name(id="Abort", ctx=ast.Load()), args=[], keywords=[]))
        self.current_function.irbuilder.unreachable()
        self.current_function.irbuilder.position_at_end(is_ok_block)

    def visit(self, node, should_load=False):
        self.should_load_stack.append(should_load)
        ret = super().visit(node)
        self.should_load_stack.pop()
        return ret

    def visit_Subscript(self, node):
        assert self.is_inside_function
        assert isinstance(node.value, ast.Name)
        arr = self.get_array_variable(node.value.id)
        index = self.visit(node.slice)
        self.emit_check_bounds(index, arr.operands[0])
        ptr = self.current_function.irbuilder.gep(arr, [index])
        if self.should_load_stack[-1] == True:
            return self.current_function.irbuilder.load(ptr)
        return ptr

def compile_llvm_module(llvm_module):
    llvm_ir_str = str(llvm_module)
    llvm_module = llvm.parse_assembly(llvm_ir_str)
    llvm_module.verify()
    target = llvm.Target.from_triple(llvm.get_default_triple())
    target_machine = target.create_target_machine()
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    engine.add_module(llvm_module)
    engine.finalize_object()
    engine.run_static_constructors()
    return engine

def chall_main():
    COMPILED_PROGRAMS = []
    while True:
        print("1) To compile a program")
        print("2) To execute a program")
        choice = input("menu>\n").strip()
        if choice == '1':
            program_source = base64.b64decode(input("Insert program>\n")).decode()
            parsed_program = ast.parse(program_source)
            visitor = ASTVisitor()
            llvm_mod = visitor(parsed_program)
            COMPILED_PROGRAMS.append(compile_llvm_module(llvm_mod))
            if len(COMPILED_PROGRAMS) > 4:
                print("Stop compiling random stuffs just solve the chall ty")
                return
        elif choice == '2':
            idx = int(input("Insert idx>\n").strip())
            engine = COMPILED_PROGRAMS[idx]
            param = int(input("Insert arg>\n").strip())
            main_func_ptr = engine.get_function_address("main")
            cfunc = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_uint64)(main_func_ptr)
            print("output: ", hex(cfunc(param) & 0xffffffffffffffff))
        else:
            print("bye bye")
            return

chall_main()