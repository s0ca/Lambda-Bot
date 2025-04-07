let questionCount = 0;

function addQuestion() {
    const form = document.getElementById("quiz-form");
    const block = document.createElement("div");
    block.className = "question-block";
    block.innerHTML = \`
        <label>Question :</label>
        <input type="text" name="question-\${questionCount}" required />
        <div class="choices">
            <label>Choix :</label>
            <input type="text" name="choice-\${questionCount}-0" required />
            <input type="text" name="choice-\${questionCount}-1" required />
            <input type="text" name="choice-\${questionCount}-2" required />
            <input type="text" name="choice-\${questionCount}-3" required />
        </div>
        <div class="choice-buttons">
            <label>Bonne réponse :</label><br/>
            <button type="button" onclick="selectAnswer(this, \${questionCount}, 0)">Choix 1</button>
            <button type="button" onclick="selectAnswer(this, \${questionCount}, 1)">Choix 2</button>
            <button type="button" onclick="selectAnswer(this, \${questionCount}, 2)">Choix 3</button>
            <button type="button" onclick="selectAnswer(this, \${questionCount}, 3)">Choix 4</button>
        </div>
        <input type="hidden" name="answer-\${questionCount}" value="-1" />
    \`;
    form.appendChild(block);
    questionCount++;
}

function selectAnswer(btn, qIndex, answerIndex) {
    const buttons = btn.parentElement.querySelectorAll("button");
    buttons.forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    document.querySelector(\`input[name="answer-\${qIndex}"]\`).value = answerIndex;
}

function downloadJSON() {
    const data = [];
    for (let i = 0; i < questionCount; i++) {
        const question = document.querySelector(\`input[name="question-\${i}"]\`)?.value;
        const choices = [];
        for (let j = 0; j < 4; j++) {
            choices.push(document.querySelector(\`input[name="choice-\${i}-\${j}"]\`)?.value);
        }
        const answer = parseInt(document.querySelector(\`input[name="answer-\${i}"]\`)?.value, 10);
        if (question && choices.every(c => c !== "") && answer >= 0 && answer < 4) {
            data.push({ question, choices, answer_index: answer });
        }
    }
    const blob = new Blob([JSON.stringify(data, null, 4)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "quiz.json";
    link.click();
}
