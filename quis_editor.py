import json
from pathlib import Path

QUIZ_FILE = Path("data/quiz_questions.json")


def load_questions():
    if QUIZ_FILE.exists():
        with open(QUIZ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_questions(questions):
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
    print("✅ Fichier sauvegardé avec succès.")


def list_questions(questions):
    for i, q in enumerate(questions):
        print(f"\n[{i}] {q['question']}")
        for idx, choice in enumerate(q["choices"]):
            correct = " ✅" if idx == q["answer_index"] else ""
            print(f"  {idx}. {choice}{correct}")


def add_question(questions):
    question = input("Question : ").strip()
    choices = []
    for i in range(4):
        choices.append(input(f"Choix {i} : ").strip())

    while True:
        try:
            answer = int(input("Index de la bonne réponse (0-3) : "))
            if 0 <= answer < 4:
                break
            else:
                print("⚠️ Doit être entre 0 et 3.")
        except ValueError:
            print("⚠️ Entrez un entier.")

    questions.append({
        "question": question,
        "choices": choices,
        "answer_index": answer
    })
    print("🧠 Question ajoutée !")


def delete_question(questions):
    list_questions(questions)
    try:
        idx = int(input("Index de la question à supprimer : "))
        q = questions.pop(idx)
        print(f"🗑️ Supprimé : {q['question']}")
    except (ValueError, IndexError):
        print("❌ Index invalide.")


def main():
    questions = load_questions()

    while True:
        print("\n=== ÉDITEUR DE QUIZ ===")
        print("1. Lister les questions")
        print("2. Ajouter une question")
        print("3. Supprimer une question")
        print("4. Sauvegarder et quitter")
        print("5. Quitter sans sauvegarder")

        choice = input("> ").strip()

        if choice == "1":
            list_questions(questions)
        elif choice == "2":
            add_question(questions)
        elif choice == "3":
            delete_question(questions)
        elif choice == "4":
            save_questions(questions)
            break
        elif choice == "5":
            print("👋 Au revoir sans sauvegarde.")
            break
        else:
            print("❌ Choix invalide.")


if __name__ == "__main__":
    main()
