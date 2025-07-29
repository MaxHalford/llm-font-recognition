# Do LLMs recognise fonts?

This is a live benchmark of various LLMs' ability to recognise fonts from images.
The latter are scraped from [dafont.com](https://www.dafont.com/forum/?f=1). Each LLM is asked to
identify the font whenever a new image is uploaded by a user. The guesses are compared against the
actual font, once it has been identified by someone and confirmed. This process avoids benchmark
contamination.

The source code for this benchmark is available on [GitHub](https://github.com/MaxHalford/llm-font-recognition).

```js
const tasks = FileAttachment("data/tasks.json").json({typed: true});
const guesses = FileAttachment("data/guesses.json").json({typed: true});
const lastScrapedAt = FileAttachment("data/last_scraped_at.json").json({typed: true});
```

*Updated at ${lastScrapedAt.last_scraped_at}*

```js
const getModelGuesses = (modelName) => {
  return guesses.filter((guess) => guess.model_name === modelName && getTask(guess.task_id).identified_font !== null);
};

const getCandidates = (guess) => {
    return [
        guess.candidate_font_1,
        guess.candidate_font_2,
        guess.candidate_font_3,
        guess.candidate_font_4,
        guess.candidate_font_5
    ];
};

const getTask = (taskId) => {
  return tasks.find((task) => task.task_id === taskId);
};

const getTopKAccuracy = (modelName, k) => {
  const modelGuesses = getModelGuesses(modelName);
  let correctGuesses = 0;
  for (const guess of modelGuesses) {
    const candidates = getCandidates(guess);
    if (candidates.slice(0, k).includes(getTask(guess.task_id).identified_font)) {
      correctGuesses += 1
    }
  }
  return d3.format(".2%")(correctGuesses / modelGuesses.length);
};
```

<h2>gpt-4o-mini</h2>

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Predictions</h2>
    <span class="big">${getModelGuesses("gpt-4o-mini").length}</span>
  </div>
  <div class="card">
    <h2>Top-1 accuracy</h2>
    <span class="big">${getTopKAccuracy("gpt-4o-mini", 1)}</span>
  </div>
  <div class="card">
    <h2>Top-2 accuracy</h2>
    <span class="big">${getTopKAccuracy("gpt-4o-mini", 2)}</span>
  </div>
  <div class="card">
    <h2>Top-3 accuracy</h2>
    <span class="big">${getTopKAccuracy("gpt-4o-mini", 3)}</span>
  </div>
  <div class="card">
    <h2>Top-4 accuracy</h2>
    <span class="big">${getTopKAccuracy("gpt-4o-mini", 4)}</span>
  </div>
  <div class="card">
    <h2>Top-5 accuracy</h2>
    <span class="big">${getTopKAccuracy("gpt-4o-mini", 5)}</span>
  </div>
</div>

<h2>gemini-2.5-flash-preview-05-20</h2>

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Predictions</h2>
    <span class="big">${getModelGuesses("gemini-2.5-flash-preview-05-20").length}</span>
  </div>
  <div class="card">
    <h2>Top-1 accuracy</h2>
    <span class="big">${getTopKAccuracy("gemini-2.5-flash-preview-05-20", 1)}</span>
  </div>
  <div class="card">
    <h2>Top-2 accuracy</h2>
    <span class="big">${getTopKAccuracy("gemini-2.5-flash-preview-05-20", 2)}</span>
  </div>
  <div class="card">
    <h2>Top-3 accuracy</h2>
    <span class="big">${getTopKAccuracy("gemini-2.5-flash-preview-05-20", 3)}</span>
  </div>
  <div class="card">
    <h2>Top-4 accuracy</h2>
    <span class="big">${getTopKAccuracy("gemini-2.5-flash-preview-05-20", 4)}</span>
  </div>
  <div class="card">
    <h2>Top-5 accuracy</h2>
    <span class="big">${getTopKAccuracy("gemini-2.5-flash-preview-05-20", 5)}</span>
  </div>
</div>
