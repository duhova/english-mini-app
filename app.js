// Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// Получение параметров из URL
const urlParams = new URLSearchParams(window.location.search);
let user_id = urlParams.get('user_id');
let lives = parseInt(urlParams.get('lives')) || 3;
let currentLevelFromUrl = urlParams.get('level') || null;

// Элементы для отображения жизней
const livesDisplay = document.getElementById('livesDisplay');
const livesDisplayTest = document.getElementById('livesDisplayTest');

function updateLivesUI() {
    const livesText = `❤️ Жизни: ${lives}`;
    if (livesDisplay) livesDisplay.textContent = livesText;
    if (livesDisplayTest) livesDisplayTest.textContent = livesText;
}
updateLivesUI();

// Глобальные переменные
let currentLevel = '';
let currentTest = [];
let currentQuestionIndex = 0;
let userAnswers = {};
let correctCount = 0;
let points = 0;
let streak = 0;
let achievements = [];
let testResults = [];

// Инициализация Telegram BackButton
function showBackButton() {
    tg.BackButton.show();
    tg.BackButton.onClick(() => {
        goBackToLevels();
    });
}
function hideBackButton() {
    tg.BackButton.hide();
}

// Загрузка тестов
async function loadTests(level) {
    try {
        const response = await fetch('tests.json');
        if (!response.ok) throw new Error('Ошибка загрузки');
        const data = await response.json();
        return data[level] || [];
    } catch (e) {
        console.error(e);
        return [];
    }
}

// Старт теста
async function startTest(level) {
    currentLevel = level;
    currentQuestionIndex = 0;
    userAnswers = {};
    correctCount = 0;
    streak = 0;
    achievements = [];
    testResults = [];

    showBackButton();

    document.getElementById('levelSelect').style.display = 'none';
    document.getElementById('loadingScreen').style.display = 'flex';

    currentTest = await loadTests(level);

    if (!currentTest.length) {
        alert('Ошибка загрузки тестов');
        goBackToLevels();
        return;
    }

    document.getElementById('loadingScreen').style.display = 'none';
    document.getElementById('testContainer').style.display = 'block';

    document.getElementById('totalQuestions').textContent = currentTest.length;
    updateLivesUI();
    loadQuestion();
    updateProgress();
}

// Загрузка вопроса
function loadQuestion() {
    const q = currentTest[currentQuestionIndex];

    document.getElementById('questionText').textContent =
        `Вопрос ${currentQuestionIndex + 1}: ${q.question}`;

    const container = document.getElementById('optionsContainer');
    container.innerHTML = '';

    q.options.forEach((opt, i) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';

        if (userAnswers[currentQuestionIndex] !== undefined) {
            btn.classList.add('disabled');
            if (i === q.correct) btn.classList.add('correct');
            if (userAnswers[currentQuestionIndex] === i && i !== q.correct)
                btn.classList.add('wrong');
        }

        if (userAnswers[currentQuestionIndex] === i)
            btn.classList.add('selected');

        btn.innerHTML = `<b>${String.fromCharCode(65 + i)}.</b> ${opt}`;

        if (userAnswers[currentQuestionIndex] === undefined) {
            btn.onclick = () => selectOption(i);
        }

        container.appendChild(btn);
    });

    document.getElementById('prevBtn').disabled = currentQuestionIndex === 0;

    if (userAnswers[currentQuestionIndex] !== undefined) {
        document.getElementById('checkBtn').style.display = 'none';
        document.getElementById('nextBtn').style.display = 'block';
        showFeedback();
    } else {
        document.getElementById('checkBtn').style.display = 'block';
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById('feedback').style.display = 'none';
    }

    document.getElementById('hintBtn').disabled =
        userAnswers[currentQuestionIndex] !== undefined;

    updateProgress();
}

function selectOption(i) {
    userAnswers[currentQuestionIndex] = i;

    document.querySelectorAll('.option-btn')
        .forEach(btn => btn.classList.remove('selected'));

    document.querySelectorAll('.option-btn')[i].classList.add('selected');
}

function checkAnswer() {
    if (userAnswers[currentQuestionIndex] === undefined) {
        alert('Выберите ответ');
        return;
    }

    const q = currentTest[currentQuestionIndex];
    const selected = userAnswers[currentQuestionIndex];
    const isCorrect = selected === q.correct;

    if (!isCorrect) {
        lives = Math.max(0, lives - 1);
        updateLivesUI();
        if (lives === 0) {
            alert("💀 У вас закончились жизни! Тест остановлен.");
            showResults();
            return;
        }
    }

    testResults[currentQuestionIndex] = {
        question: q.question,
        userAnswer: selected,
        correctAnswer: q.correct,
        isCorrect: isCorrect,
        explanation: q.explanation || ''
    };

    if (isCorrect) {
        correctCount++;
        points += 10;
        streak++;
        if (streak === 3) {
            points += 20;
            achievements.push('🔥 Серия из 3!');
        }
    } else {
        streak = 0;
    }

    document.getElementById('correctCount').textContent = correctCount;
    showFeedback();

    document.getElementById('checkBtn').style.display = 'none';
    document.getElementById('nextBtn').style.display = 'block';
    document.getElementById('hintBtn').disabled = true;

    document.querySelectorAll('.option-btn')
        .forEach(btn => {
            btn.classList.add('disabled');
            btn.onclick = null;
        });
}

function showHint() {
    const q = currentTest[currentQuestionIndex];
    if (!q.hint) {
        alert('Нет подсказки');
        return;
    }
    alert('💡 ' + q.hint);
}

function showFeedback() {
    const q = currentTest[currentQuestionIndex];
    const selected = userAnswers[currentQuestionIndex];
    const isCorrect = selected === q.correct;

    const feedback = document.getElementById('feedback');
    feedback.className = isCorrect ? 'feedback correct' : 'feedback incorrect';

    document.getElementById('feedbackTitle').innerHTML =
        isCorrect ? '✅ Правильно' : '❌ Неправильно';

    document.getElementById('explanation').innerHTML =
        `<b>Ответ:</b> ${q.options[q.correct]}<br>${q.explanation || ''}`;

    feedback.style.display = 'block';
}

function nextQuestion() {
    if (currentQuestionIndex < currentTest.length - 1) {
        currentQuestionIndex++;
        loadQuestion();
    } else {
        showResults();
    }
}

function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        loadQuestion();
    }
}

function updateProgress() {
    const progress = ((currentQuestionIndex + 1) / currentTest.length) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
}

function showResults() {
    const total = currentTest.length;
    const percentage = Math.round((correctCount / total) * 100);

    if (percentage === 100) {
        achievements.push('🏆 Идеально!');
        points += 50;
    }
    if (percentage >= 80) {
        achievements.push('⭐ Отличный результат');
    }

    document.getElementById('scoreText').textContent = `${correctCount}/${total}`;
    document.getElementById('pointsText').textContent = points + ' XP';

    const achievementsContainer = document.getElementById('achievementsList');
    achievementsContainer.innerHTML = '';
    achievements.forEach(a => {
        const div = document.createElement('div');
        div.textContent = a;
        achievementsContainer.appendChild(div);
    });

    document.getElementById('testContainer').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'block';

    sendResultsToBot(percentage);
}

function sendResultsToBot(percentage) {
    const data = {
        level: currentLevel,
        score: correctCount,
        total: currentTest.length,
        percentage: percentage,
        lives: lives,
        user_id: user_id
    };
    if (tg.sendData) {
        tg.sendData(JSON.stringify(data));
    }
}

function goBackToLevels() {
    hideBackButton();
    document.getElementById('levelSelect').style.display = 'block';
    document.getElementById('testContainer').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('loadingScreen').style.display = 'none';
}

// Автоматический старт, если передан уровень в URL
if (currentLevelFromUrl) {
    startTest(currentLevelFromUrl);
} else {
    // Иначе показываем выбор уровня и привязываем обработчики
    document.querySelectorAll('.level-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            startTest(btn.dataset.level);
        });
    });
}

tg.ready();