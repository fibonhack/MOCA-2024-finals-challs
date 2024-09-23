use jolt_sdk::RV32IHyraxProof;

pub fn main() {
    let (prove_two_plus_two, _verify_two_plus_two) = guest::build_two_plus_two();
    let (output, proof_gen) = prove_two_plus_two();
    println!("Proof generated! {}", output);
    let proof_bytes = proof_gen.serialize_to_bytes().unwrap();
    println!("{}", hex::encode(&proof_bytes));
}
