# Mock clinical guidelines for local RAG ingest. Not medical advice.

MOCK_CLINICAL_GUIDELINES = [
    {
        "category": "SKIN",
        "sub_category": "acne",
        "condition_name": "Comedonal and mild inflammatory acne",
        "document_text": (
            "Protocol for comedonal and mild inflammatory acne vulgaris (face and neck). "
            "Presents with open and closed comedones, occasional papules, and oily T-zone. "
            "First-line topicals: salicylic acid 2% for pore unclogging, benzoyl peroxide 2.5-5% against C. acnes, "
            "and niacinamide 5-10% to reduce sebum and post-inflammatory marks. "
            "Use a gentle non-comedogenic cleanser twice daily; introduce retinoid-class actives at night if tolerated. "
            "Do not combine high-strength retinoids with AHA/BHA in the same routine. "
            "Stop benzoyl peroxide if severe dryness, peeling, or contact dermatitis develops."
        ),
        "metadata": {
            "target": "face",
            "severity": "mild_to_moderate",
            "symptoms": ["comedones", "papules", "oiliness"],
        },
    },
    {
        "category": "SKIN",
        "sub_category": "rosacea",
        "condition_name": "Rosacea and facial erythema",
        "document_text": (
            "Protocol for rosacea-prone facial flushing and persistent central-face redness. "
            "Symptoms include burning, stinging, visible capillaries, and flares after heat, spicy food, or alcohol. "
            "Soothing actives: azelaic acid 10-15%, centella asiatica, allantoin, and ceramide-dominant moisturizers. "
            "Avoid glycolic peels, physical scrubs, menthol, alcohol toners, and fragrance. "
            "Mineral sunscreen daily. Escalate to a clinician if papulopustular lesions, ocular symptoms, or phymatous change appear."
        ),
        "metadata": {
            "target": "face",
            "severity": "mild_to_moderate",
            "symptoms": ["redness", "flushing", "burning"],
        },
    },
    {
        "category": "SKIN",
        "sub_category": "barrier",
        "condition_name": "Compromised skin barrier and atopic-prone dryness",
        "document_text": (
            "Protocol for impaired barrier and atopic-prone dry, itchy skin. "
            "Findings include tightness, fine scale, stinging with products, and itch worse in low humidity. "
            "Repair with ceramides (approximately 1:3:1 ceramide-cholesterol-fatty acid), petrolatum or shea occlusives, "
            "glycerin or hyaluronic acid humectants, and colloidal oatmeal. "
            "Limit hot showers and foaming sulfate cleansers. Pause acids and retinoids until sting resolves. "
            "Seek care for oozing, crusting, or rapidly spreading erythema suggesting infection."
        ),
        "metadata": {
            "target": "body_and_face",
            "severity": "mild_to_moderate",
            "symptoms": ["dryness", "itch", "stinging"],
        },
    },
    {
        "category": "SKIN",
        "sub_category": "pigment",
        "condition_name": "Melasma and post-inflammatory hyperpigmentation",
        "document_text": (
            "Protocol for epidermal melanosis: melasma patches and post-inflammatory hyperpigmentation. "
            "Strict daily broad-spectrum SPF 50+, hats, and shade. "
            "Brightening options: azelaic acid 10-20%, vitamin C (ascorbic acid), niacinamide, and low-strength glycolic acid under 10% if barrier is intact. "
            "Hydroquinone only under clinician supervision and not during pregnancy. "
            "Avoid picking acne lesions. Improvement is slow (8-12 weeks); photoprotection is non-negotiable."
        ),
        "metadata": {
            "target": "face",
            "severity": "mild_to_moderate",
            "symptoms": ["dark_patches", "uneven_tone"],
        },
    },
    {
        "category": "SKIN",
        "sub_category": "safety",
        "condition_name": "Pregnancy-safe topical restrictions for skin",
        "document_text": (
            "Skin protocol safety in pregnancy and lactation. "
            "Avoid topical retinoids (tretinoin, adapalene, tazarotene), oral isotretinoin, spironolactone, "
            "and high-dose hydroquinone. "
            "Generally preferred alternatives for pregnancy acne and pigment: azelaic acid 10-15%, "
            "glycolic acid under 10%, vitamin C, and bland barrier moisturizers. "
            "Benzoyl peroxide may be used sparingly on limited areas if a clinician agrees. "
            "Do not start new prescription topicals without obstetric and dermatology review."
        ),
        "metadata": {
            "target": "face",
            "risk": "high",
            "population": "pregnancy_lactation",
        },
    },
    {
        "category": "HAIR",
        "sub_category": "alopecia",
        "condition_name": "Androgenetic alopecia pattern thinning",
        "document_text": (
            "Protocol for androgenetic alopecia: progressive miniaturization at crown, mid-scalp, and frontal hairline. "
            "First-line topical minoxidil 5% for men and 2-5% for women, applied to dry scalp. "
            "Adjuncts: caffeine scalp serum, Redensyl-class leave-ons, and ketoconazole 1-2% shampoo two to three times weekly "
            "to reduce scalp DHT-related inflammation and flaking. "
            "Expect 3-6 months before density change. Do not use topical minoxidil in unmanaged severe hypertension "
            "or if the patient reports chest pain, dizziness, or unwanted facial hypertrichosis that they cannot tolerate."
        ),
        "metadata": {
            "target": "scalp",
            "severity": "mild_to_moderate",
            "symptoms": ["thinning", "widening_part", "receding_hairline"],
        },
    },
    {
        "category": "HAIR",
        "sub_category": "shedding",
        "condition_name": "Telogen effluvium diffuse shedding",
        "document_text": (
            "Protocol for telogen effluvium: abrupt diffuse shedding 2-3 months after illness, crash dieting, "
            "post-partum, surgery, or major psychological stress. Pull test often positive; scalp usually looks normal. "
            "Reassure that follicles typically re-enter anagen; recovery often 6-12 months if the trigger has resolved. "
            "Support with adequate protein, iron studies if fatigue or heavy menses, gentle handling, and avoiding tight styles. "
            "Do not start aggressive minoxidil solely for acute TE without ruling out patterned androgenetic overlap. "
            "Refer if scarring, patchy bald spots, or systemic red flags (weight loss, fever, thyroid symptoms)."
        ),
        "metadata": {
            "target": "scalp",
            "severity": "acute_to_subacute",
            "symptoms": ["diffuse_shedding", "increased_hair_on_pillow"],
        },
    },
    {
        "category": "HAIR",
        "sub_category": "scalp",
        "condition_name": "Seborrheic dermatitis of the scalp",
        "document_text": (
            "Protocol for scalp seborrheic dermatitis: greasy yellow scale, itch, and erythema of scalp, brows, or nuchal hairline. "
            "Antifungal and keratolytic shampoos: ketoconazole 2%, zinc pyrithione, or salicylic acid 2-3%. "
            "Use 2-3 times weekly, leave on the scalp 5 minutes, then rinse. Rotate with a gentle cleanser on other days. "
            "Avoid heavy coconut or olive oils on active flaking; Malassezia can worsen with lipids. "
            "If thick scale or oozing, consider clinician-directed anti-inflammatory scalp therapy rather than more oiling."
        ),
        "metadata": {
            "target": "scalp",
            "severity": "mild_to_moderate",
            "symptoms": ["flaking", "itch", "greasy_scale"],
        },
    },
    {
        "category": "HAIR",
        "sub_category": "safety",
        "condition_name": "Pregnancy and minoxidil safety for hair protocols",
        "document_text": (
            "Hair protocol safety in pregnancy and lactation. "
            "Do not start or continue topical or oral minoxidil in pregnancy unless a specialist explicitly directs it; "
            "minoxidil is generally avoided due to fetal and hemodynamic concerns. "
            "Defer anti-androgen hair therapies (spironolactone, finasteride, dutasteride) entirely in pregnancy; "
            "finasteride is contraindicated and a teratogenic risk for male fetuses. "
            "Prefer diagnosing trigger-related postpartum shedding (telogen) before aggressive stimulation. "
            "Gentle cleansing, nutrition, and treating seborrheic scale are acceptable supportive measures."
        ),
        "metadata": {
            "target": "scalp",
            "risk": "high",
            "population": "pregnancy_lactation",
        },
    },
]
