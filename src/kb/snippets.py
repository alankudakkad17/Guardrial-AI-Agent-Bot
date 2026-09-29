"""Curated knowledge base for the guardrailed medical assistant.

Intentionally small (~18 snippets) so retrieval quality and grounding
behavior can be reasoned about by hand. General information only —
no dosage-by-weight or individualized instructions.
"""

SNIPPETS = [
    # --- General medication information ---
    {
        "id": "med_001",
        "category": "drug_info",
        "title": "Ibuprofen — overview",
        "text": (
            "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to "
            "relieve pain, reduce inflammation, and lower fever. It is available "
            "over the counter in most countries. Common side effects include "
            "stomach upset, heartburn, and increased risk of gastrointestinal "
            "bleeding with prolonged use."
        ),
    },
    {
        "id": "med_002",
        "category": "drug_info",
        "title": "Acetaminophen (Paracetamol) — overview",
        "text": (
            "Acetaminophen (known as paracetamol outside the US) relieves pain "
            "and reduces fever but has minimal anti-inflammatory effect. It does "
            "not typically cause stomach irritation. Taking more than the "
            "recommended maximum daily amount can cause serious liver damage, "
            "especially when combined with alcohol."
        ),
    },
    {
        "id": "med_003",
        "category": "drug_info",
        "title": "Amoxicillin — overview",
        "text": (
            "Amoxicillin is a penicillin-class antibiotic used to treat a range "
            "of bacterial infections, including ear infections, strep throat, "
            "and some respiratory infections. Common side effects include "
            "diarrhea, nausea, and rash. It is not effective against viral "
            "infections such as the common cold or flu."
        ),
    },
    {
        "id": "med_004",
        "category": "drug_info",
        "title": "Loratadine — overview",
        "text": (
            "Loratadine is a second-generation antihistamine used to relieve "
            "allergy symptoms such as sneezing, runny nose, and itchy eyes. "
            "Unlike older antihistamines, it causes little to no drowsiness in "
            "most people at typical doses."
        ),
    },
    {
        "id": "med_005",
        "category": "drug_info",
        "title": "Omeprazole — overview",
        "text": (
            "Omeprazole is a proton pump inhibitor (PPI) that reduces stomach "
            "acid production. It is commonly used for heartburn, acid reflux "
            "(GERD), and stomach ulcers. Long-term use has been associated with "
            "reduced absorption of vitamin B12 and magnesium."
        ),
    },
    {
        "id": "med_006",
        "category": "drug_info",
        "title": "Metformin — overview",
        "text": (
            "Metformin is a first-line oral medication for type 2 diabetes that "
            "works by reducing glucose production in the liver and improving "
            "insulin sensitivity. Common side effects include gastrointestinal "
            "upset, particularly when treatment is first started."
        ),
    },
    {
        "id": "med_007",
        "category": "drug_info",
        "title": "Sertraline — overview",
        "text": (
            "Sertraline is a selective serotonin reuptake inhibitor (SSRI) used "
            "to treat depression, anxiety disorders, and other mood conditions. "
            "It typically takes several weeks of consistent use before its full "
            "effect is noticeable. Common side effects include nausea, "
            "insomnia, and sexual side effects."
        ),
    },
    {
        "id": "med_008",
        "category": "drug_info",
        "title": "Albuterol (Salbutamol) — overview",
        "text": (
            "Albuterol is a short-acting beta-agonist inhaler used to relieve "
            "sudden asthma or COPD symptoms such as wheezing and shortness of "
            "breath. Effects are usually felt within minutes. Common side "
            "effects include jitteriness and a fast heartbeat."
        ),
    },
    # --- Drug interaction facts ---
    {
        "id": "int_001",
        "category": "interaction",
        "title": "NSAIDs and blood thinners",
        "text": (
            "Taking NSAIDs (such as ibuprofen) together with blood-thinning "
            "medications like warfarin significantly increases the risk of "
            "gastrointestinal and other bleeding. This combination is generally "
            "avoided unless specifically directed by a clinician."
        ),
    },
    {
        "id": "int_002",
        "category": "interaction",
        "title": "Acetaminophen and alcohol",
        "text": (
            "Regular or heavy alcohol use combined with acetaminophen increases "
            "the risk of liver toxicity, even at standard acetaminophen doses. "
            "People who drink heavily are generally advised to limit or avoid "
            "acetaminophen."
        ),
    },
    {
        "id": "int_003",
        "category": "interaction",
        "title": "SSRIs and MAOIs",
        "text": (
            "Combining SSRIs like sertraline with monoamine oxidase inhibitors "
            "(MAOIs) can cause serotonin syndrome, a potentially "
            "life-threatening condition. A washout period is typically required "
            "when switching between these drug classes."
        ),
    },
    {
        "id": "int_004",
        "category": "interaction",
        "title": "Grapefruit and statins",
        "text": (
            "Grapefruit and grapefruit juice can interfere with the enzyme that "
            "metabolizes many statin medications, potentially raising drug "
            "levels in the blood and increasing the risk of side effects such "
            "as muscle damage."
        ),
    },
    {
        "id": "int_005",
        "category": "interaction",
        "title": "Antibiotics and oral contraceptives",
        "text": (
            "Certain antibiotics, particularly rifampin, can reduce the "
            "effectiveness of oral contraceptives. Most other common "
            "antibiotics, including amoxicillin, have limited evidence of "
            "meaningfully reducing contraceptive effectiveness, but "
            "manufacturers often still advise backup contraception out of "
            "caution."
        ),
    },
    # --- Triage red-flag symptoms ---
    {
        "id": "triage_001",
        "category": "triage",
        "title": "Chest pain with shortness of breath",
        "text": (
            "Chest pain combined with shortness of breath, sweating, nausea, or "
            "pain radiating to the arm or jaw can indicate a heart attack. This "
            "combination of symptoms is a medical emergency and warrants "
            "immediate emergency care."
        ),
    },
    {
        "id": "triage_002",
        "category": "triage",
        "title": "Sudden severe headache",
        "text": (
            "A sudden, severe headache described as 'the worst headache of my "
            "life,' especially with neck stiffness, vision changes, or "
            "confusion, can indicate a stroke or brain hemorrhage and requires "
            "emergency evaluation."
        ),
    },
    {
        "id": "triage_003",
        "category": "triage",
        "title": "Signs of stroke (FAST)",
        "text": (
            "Facial drooping, arm weakness, and slurred or difficult speech are "
            "classic warning signs of stroke. Time of symptom onset matters "
            "greatly for treatment, so emergency services should be called "
            "immediately if these signs appear."
        ),
    },
    {
        "id": "triage_004",
        "category": "triage",
        "title": "Severe allergic reaction (anaphylaxis)",
        "text": (
            "Difficulty breathing, swelling of the face or throat, widespread "
            "hives, or dizziness after exposure to an allergen (food, insect "
            "sting, medication) can indicate anaphylaxis, a life-threatening "
            "emergency requiring immediate treatment, often with epinephrine."
        ),
    },
    {
        "id": "triage_005",
        "category": "triage",
        "title": "High fever in infants",
        "text": (
            "A fever above 100.4°F (38°C) in an infant under 3 months old is "
            "considered a medical emergency and warrants immediate evaluation, "
            "since infants can deteriorate quickly from infections that would "
            "be minor in older children or adults."
        ),
    },
    {
        "id": "triage_006",
        "category": "triage",
        "title": "Severe abdominal pain",
        "text": (
            "Sudden, severe abdominal pain — particularly if it is localized to "
            "the lower right abdomen, or accompanied by fever, vomiting, or a "
            "rigid abdomen — can indicate conditions such as appendicitis and "
            "should be evaluated urgently."
        ),
    },
]
