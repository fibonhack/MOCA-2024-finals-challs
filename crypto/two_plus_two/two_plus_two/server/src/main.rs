use jolt_sdk::RV32IHyraxProof;

pub fn main() {
    let (_prove_two_plus_two, verify_two_plus_two) = guest::build_two_plus_two();

    println!("Can you prove that 2+2=5?");

    let line = std::io::stdin().lines().next().unwrap().unwrap();
    if line.len() == 0 {
        println!("k thx bye");
        return;
    }

    let proof = RV32IHyraxProof::deserialize_from_bytes(&hex::decode(line).unwrap()).unwrap();

    let inputs = &proof.proof.program_io.inputs;
    println!("inputs: {:?}", inputs);
    assert_eq!(inputs.len(), 0);

    let outputs = &proof.proof.program_io.outputs;
    println!("outputs: {:?}", outputs);
    assert_eq!(outputs.len(), 1);
    assert_eq!(outputs[0], 5); // 2+2 is 5!

    let panics = &proof.proof.program_io.panic;
    println!("panics: {:?}", panics);
    assert!(!panics);

    println!("Verifying the proof...");
    let is_valid = verify_two_plus_two(proof);
    if is_valid {
        println!("The proof is valid!");
        println!("FLAG: {}", std::env::var("FLAG").unwrap());
    } else {
        println!("The proof is invalid! :(");
    }
}
