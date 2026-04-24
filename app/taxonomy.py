"""
Predefined tag taxonomy.  arXiv category → top-level slug mapping drives
ingestion auto-tagging; the full subtopic list is passed to the LLM so it can
pick the most precise tags.
"""

TAXONOMY: dict[str, dict] = {
    "artificial-intelligence": {
        "label": "Artificial Intelligence",
        "description": "Machine learning, deep learning, neural networks, and AI systems",
        "arxiv_categories": ["cs.AI", "cs.LG", "cs.NE"],
        "subtopics": [
            "machine-learning",
            "deep-learning",
            "reinforcement-learning",
            "computer-vision",
            "natural-language-processing",
            "robotics",
            "generative-ai",
            "ai-alignment",
        ],
    },
    "mathematics": {
        "label": "Mathematics",
        "description": "Pure and applied mathematics",
        "arxiv_categories": ["math.CO", "math.ST", "math.OC", "math.NT", "math.AG", "math.PR"],
        "subtopics": [
            "combinatorics",
            "statistics",
            "optimization",
            "number-theory",
            "algebra",
            "geometry",
            "probability",
            "topology",
        ],
    },
    "physics": {
        "label": "Physics",
        "description": "Theoretical and experimental physics",
        "arxiv_categories": ["hep-ph", "hep-th", "cond-mat", "quant-ph", "astro-ph.CO", "gr-qc"],
        "subtopics": [
            "quantum-computing",
            "quantum-mechanics",
            "cosmology",
            "condensed-matter",
            "particle-physics",
            "astrophysics",
            "general-relativity",
        ],
    },
    "biology": {
        "label": "Biology",
        "description": "Life sciences, genomics, and neuroscience",
        "arxiv_categories": ["q-bio.BM", "q-bio.GN", "q-bio.NC", "q-bio.PE"],
        "subtopics": [
            "genomics",
            "neuroscience",
            "computational-biology",
            "bioinformatics",
            "structural-biology",
            "systems-biology",
            "evolution",
        ],
    },
    "computer-science": {
        "label": "Computer Science",
        "description": "Algorithms, systems, security, and software",
        "arxiv_categories": ["cs.DS", "cs.CR", "cs.DC", "cs.PL", "cs.SE", "cs.DB", "cs.NI"],
        "subtopics": [
            "algorithms",
            "cryptography",
            "distributed-systems",
            "programming-languages",
            "databases",
            "networking",
            "software-engineering",
        ],
    },
    "economics": {
        "label": "Economics",
        "description": "Economic theory, econometrics, and finance",
        "arxiv_categories": ["econ.GN", "econ.EM", "econ.TH", "q-fin.GN"],
        "subtopics": [
            "microeconomics",
            "macroeconomics",
            "game-theory",
            "econometrics",
            "behavioral-economics",
            "finance",
        ],
    },
    "statistics": {
        "label": "Statistics",
        "description": "Statistical methods and theory",
        "arxiv_categories": ["stat.ML", "stat.AP", "stat.TH", "stat.ME"],
        "subtopics": [
            "bayesian-methods",
            "time-series",
            "causal-inference",
            "experimental-design",
            "nonparametric-statistics",
        ],
    },
    "electrical-engineering": {
        "label": "Electrical Engineering",
        "description": "Signal processing, control systems, and communications",
        "arxiv_categories": ["eess.SP", "eess.IV", "eess.SY", "eess.AS"],
        "subtopics": [
            "signal-processing",
            "control-systems",
            "image-processing",
            "communications",
            "audio-processing",
        ],
    },
    "climate-science": {
        "label": "Climate Science",
        "description": "Climate modeling, earth systems, and environmental science",
        "arxiv_categories": ["physics.ao-ph", "astro-ph.EP"],
        "subtopics": [
            "climate-modeling",
            "atmospheric-science",
            "ocean-science",
            "renewable-energy",
            "earth-systems",
        ],
    },
    "cognitive-science": {
        "label": "Cognitive Science",
        "description": "Cognition, neuroscience, and psychology",
        "arxiv_categories": ["q-bio.NC", "cs.HC"],
        "subtopics": [
            "cognitive-neuroscience",
            "psychology",
            "decision-making",
            "human-computer-interaction",
            "linguistics",
        ],
    },
}

# Flat list of every valid tag slug — used for LLM prompts and validation
ALL_TAGS: list[str] = list(TAXONOMY.keys()) + [
    tag for cat in TAXONOMY.values() for tag in cat["subtopics"]
]

# arXiv category → parent taxonomy slug (used at ingest time)
ARXIV_TO_TAXONOMY: dict[str, str] = {
    arxiv_cat: slug
    for slug, cat_data in TAXONOMY.items()
    for arxiv_cat in cat_data["arxiv_categories"]
}
