---
theme: dashboard
title: Breakdown
toc: false
---

# Breakdown

<!-- Load and transform the data -->

```js
const guesses = FileAttachment("data/guesses.json").json({typed: true});
const tasks = FileAttachment("data/tasks.json").json({typed: true});
```

```js
const getTask = (taskId) => {
    return tasks.find(t => t.task_id === taskId)
}
```

```js
Inputs.table(
    guesses.map(x => ({
        task_id: x.task_id,
        identified_font: getTask(x.task_id).identified_font,
        model_name: x.model_name,
        candidate_font_1: x.candidate_font_1,
        candidate_font_2: x.candidate_font_2,
        candidate_font_3: x.candidate_font_3,
        candidate_font_4: x.candidate_font_4,
        candidate_font_5: x.candidate_font_5
    })).filter(x => x.identified_font !== null),
    {
        header: {
            task_id: "Task",
            identified_font: "Font",
            model_name: "Model",
            candidate_font_1: "Guess #1",
            candidate_font_2: "Guess #2",
            candidate_font_3: "Guess #3",
            candidate_font_4: "Guess #4",
            candidate_font_5: "Guess #5"
        },
        format: {
            task_id: x => html`<a href="${getTask(x).url}" target="_blank">${x}</a>`,
        },
        select: false,
        sort: true
    }
)
```
