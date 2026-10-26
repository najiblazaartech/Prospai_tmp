SUBJECTS = [
    "Question rapide, {prenom}",
    "{prenom}, un echange ?",
    "Au sujet de {entreprise}",
    "Croisement interessant, {prenom}",
    "Une idee pour {entreprise}",
]


def default_subject(prenom: str) -> str:
    import random
    return random.choice(SUBJECTS).format(prenom=prenom.split(" ")[0] if prenom else "")
