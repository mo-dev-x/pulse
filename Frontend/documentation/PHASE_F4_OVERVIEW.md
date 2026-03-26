# 🔵 PHASE F4 OVERVIEW — CAMPUS MOOD & ANALYTICS

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** ✅ Implemented in code
**Priority:** High — The analytics dashboard is Pulse's most unique differentiator  
**Estimated Time:** 3–4 days  
**Depends on:** Phase F1 (design tokens, i18n), Chart.js CDN

> **Design principle for Phase F4:** The campus mood dashboard is not a data science tool — it's a wellness mirror. Visualisations should feel warm and approachable, not clinical. Privacy notices must be prominent, not hidden in fine print.

> **Implementation note:** The analytics page, charts, privacy banner, date picker, zone breakdown, and zone activity view are implemented. The main gap versus the original plan is translation coverage: chart labels and status strings are still mostly English in the current code.

---

## 🎯 PHASE F4 GOALS

- Build the **campus mood overview widget** — today's dominant mood, colour-coded
- Build the **daily mood trend chart** — 7-day line chart using Chart.js
- Build the **weekly mood trend chart** — last 4 weeks aggregated
- Build the **emotion breakdown donut chart** — joy / sadness / anger / fear / surprise / disgust
- Build the **per-zone mood breakdown** — list or bar chart by campus zone
- Enforce and display the **privacy threshold notice** (< 10 posts = no data)
- Build the **zone activity feed** widget

---

## 📊 PHASE F4 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| Campus mood overview widget | Must Have | ✅ Implemented | 0.5 |
| Daily mood trend (7-day line chart) | Must Have | ✅ Implemented | 1 |
| Privacy threshold notice | Must Have | ✅ Implemented | 0.5 |
| Per-zone mood breakdown | Should Have | ✅ Implemented | 0.5 |
| Emotion breakdown donut | Should Have | ✅ Implemented | 0.5 |
| Weekly trend chart | Should Have | ✅ Implemented | 0.5 |
| Zone activity feed widget | Nice to Have | ✅ Implemented via `/api/zones/<id>/activity` | 0.5 |

**Overall Phase F4 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ ~95%

## 🧩 SHIPPED IMPLEMENTATION

| Area | Shipped code |
|------|--------------|
| Analytics page | `analytics.html`, `css/analytics.css`, `js/analytics.js` |
| Charts | Chart.js loaded from CDN in `analytics.html` |
| Data sources | `/api/analytics/campus`, `/api/analytics/daily`, `/api/analytics/weekly`, `/api/zones/<id>/activity` |
| Notable deviation | Chart/status copy is still mostly English rather than fully bilingual |

---

## 📋 COMPONENT 1: Campus Mood Overview Widget

**File:** `js/analytics.js`, `css/analytics.css`  
**Route:** `analytics.html`

### Layout

```
┌────────────────────────────────────────────┐
│  🌡 Humeur du campus — Aujourd'hui          │
│                                            │
│   ╔═══════════════════════════════╗        │
│   ║   😊  Positif                 ║        │
│   ║   Campus principal · 247 posts ║        │
│   ╚═══════════════════════════════╝        │
│                                            │
│   📊 Score moyen : +0.42                   │
│   📅 Mis à jour aujourd'hui                │
└────────────────────────────────────────────┘
```

### Mood Label Mapping

| Backend Value | FR Label | EN Label | Colour Token |
|---------------|----------|----------|-------------|
| `very_positive` | Très positif 😄 | Very positive 😄 | `--color-positive` |
| `positive` | Positif 😊 | Positive 😊 | `--color-positive` (lighter) |
| `neutral` | Neutre 😐 | Neutral 😐 | `--color-neutral` |
| `negative` | Négatif 😔 | Negative 😔 | `--color-negative` (lighter) |
| `very_negative` | Très négatif 😟 | Very negative 😟 | `--color-negative` |

### Privacy Threshold

If `total_posts < 10`:

```
┌────────────────────────────────────────┐
│  🔒 Données insuffisantes              │
│                                        │
│  Au moins 10 publications sont         │
│  nécessaires pour afficher l'humeur    │
│  du campus et protéger la vie privée.  │
└────────────────────────────────────────┘
```

FR: "Au moins 10 publications sont nécessaires pour afficher les données et protéger la confidentialité."  
EN: "At least 10 posts are required to display data and protect privacy."

Backend: `GET /api/analytics/campus?date=YYYY-MM-DD`

---

## 📋 COMPONENT 2: Daily Mood Trend Chart (7-Day Line)

**Library:** Chart.js 4.x (CDN — no build step)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

### Chart Config

```javascript
function buildDailyChart(canvas, data) {
  const labels = data.map(d => formatDate(d.date));      // "Lun 10 mars"
  const scores = data.map(d => d.avg_sentiment ?? null); // null = insufficient data

  return new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: getLang() === 'fr' ? 'Score d\'humeur' : 'Mood score',
        data: scores,
        borderColor: 'var(--color-primary)',
        backgroundColor: 'rgba(230, 57, 70, 0.1)',
        tension: 0.4,
        spanGaps: false,  // null = break in line (privacy gap)
        pointRadius: 5,
        pointHoverRadius: 8,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ctx.raw === null
              ? t('analytics.insufficient_data')
              : `${t('analytics.mood_score')}: ${ctx.raw.toFixed(2)}`
          }
        }
      },
      scales: {
        y: {
          min: -1, max: 1,
          ticks: {
            callback: (v) => v === 1 ? '😊' : v === 0 ? '😐' : v === -1 ? '😟' : v
          }
        }
      }
    }
  });
}
```

### Data Loading (7 Days)

```javascript
async function loadLast7Days() {
  const promises = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - i);
    return apiFetch(`/api/analytics/daily?date=${d.toISOString().slice(0, 10)}`);
  });
  const results = await Promise.all(promises);
  return (await Promise.all(results.map(r => r?.json()))).reverse();
}
```

---

## 📋 COMPONENT 3: Emotion Breakdown Donut

Displays the 6 emotion categories from the `cardiffnlp/twitter-xlm-roberta-base-emotion` model used in Phase 6.

### Chart Config

```javascript
function buildEmotionDonut(canvas, emotionCounts) {
  const emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust'];
  const labels = {
    fr: { joy: 'Joie', sadness: 'Tristesse', anger: 'Colère',
          fear: 'Peur', surprise: 'Surprise', disgust: 'Dégoût' },
    en: { joy: 'Joy', sadness: 'Sadness', anger: 'Anger',
          fear: 'Fear', surprise: 'Surprise', disgust: 'Disgust' }
  };
  const colours = {
    joy: '#FFD93D', sadness: '#74B9FF', anger: '#E74C3C',
    fear: '#A29BFE', surprise: '#FD79A8', disgust: '#55EFC4'
  };

  return new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: emotions.map(e => labels[getLang()][e]),
      datasets: [{
        data: emotions.map(e => emotionCounts[e] ?? 0),
        backgroundColor: emotions.map(e => colours[e]),
        borderWidth: 2,
        borderColor: 'var(--color-bg)'
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: { position: 'right' }
      }
    }
  });
}
```

---

## 📋 COMPONENT 4: Per-Zone Mood Breakdown

Horizontal bar chart showing avg sentiment per campus zone.

### Layout

```
Bibliothèque      ████████░ +0.62
Cafétéria         █████░░░░ +0.31
Résidences        ████░░░░░ +0.18
Sportif PEPS      ███████░░ +0.55
Général           ██░░░░░░░ −0.12
```

### Data Source

`GET /api/analytics/campus?date=YYYY-MM-DD` returns `zone_breakdown` array:
```json
{
  "campus_mood": {...},
  "zone_breakdown": [
    { "zone_id": 1, "zone_name": "Bibliothèque", "avg_sentiment": 0.62, "total_posts": 42 }
  ]
}
```

### Zone Name Localisation

Zone names come from the backend. The backend stores a bilingual `name` field — display as-is (already bilingual at data level from the `campus_zones` table).

---

## 📋 COMPONENT 5: Weekly Trend Chart

`GET /api/analytics/weekly?week_start=YYYY-MM-DD` — call for last 4 weeks.

Bar chart (Chart.js `bar` type) — one bar per week, colour-coded by mood label.

```javascript
function buildWeeklyChart(canvas, weeklyData) {
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels: weeklyData.map(w => formatWeekLabel(w.week_start)),
      datasets: [{
        label: t('analytics.weekly_mood'),
        data: weeklyData.map(w => w.avg_sentiment ?? null),
        backgroundColor: weeklyData.map(w =>
          w.avg_sentiment > 0.2  ? 'var(--color-positive)' :
          w.avg_sentiment < -0.2 ? 'var(--color-negative)' :
                                    'var(--color-neutral)'
        ),
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      scales: { y: { min: -1, max: 1 } }
    }
  });
}
```

---

## 📋 COMPONENT 6: Full Analytics Page Layout

```
┌──────────────────────────────────────────────────────┐
│  📊 Tableau de bord — Humeur du campus               │
│                             Date: [16 mars 2026 ▾]   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Humeur du jour   │  │  Tendance 7 jours        │  │
│  │  😊 Positif      │  │  [LINE CHART]            │  │
│  │  Score: +0.42    │  │                          │  │
│  └──────────────────┘  └──────────────────────────┘  │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Émotions         │  │  Par zone                │  │
│  │ [DONUT CHART]    │  │  [HORIZONTAL BAR]        │  │
│  └──────────────────┘  └──────────────────────────┘  │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │  Tendance hebdomadaire (4 semaines)           │   │
│  │  [BAR CHART]                                  │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  🔒 Les données sont agrégées. Aucun profil          │
│     individuel n'est identifiable.                   │
└──────────────────────────────────────────────────────┘
```

### Privacy Footer (always visible)

FR: "Les données affichées sont entièrement agrégées et anonymisées. Aucun profil individuel ne peut être identifié."  
EN: "All displayed data is fully aggregated and anonymised. No individual profile can be identified."

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F4

| Action | Method | Endpoint |
|--------|--------|----------|
| Daily analytics | GET | `/api/analytics/daily?date=YYYY-MM-DD` |
| Daily by zone | GET | `/api/analytics/daily?date=YYYY-MM-DD&zone_id=X` |
| Weekly analytics | GET | `/api/analytics/weekly?week_start=YYYY-MM-DD` |
| Campus overview | GET | `/api/analytics/campus?date=YYYY-MM-DD` |
| Zone activity | GET | `/api/zones/<id>/activity` |

---

## ✅ SUCCESS CRITERIA

**Phase F4 Complete When:**

- [x] Campus mood widget displays today’s mood label with visual state styling
- [x] Privacy threshold message is shown when aggregate data is insufficient
- [x] 7-day line chart renders with `null` gaps for missing data
- [~] Emotion donut chart renders the categories, but labels are not yet fully bilingual
- [x] Per-zone breakdown renders available zones
- [x] Weekly bar chart shows the last 4 weeks
- [x] Privacy aggregate notice is visible on the analytics page
- [~] Chart labels and status strings are not yet fully bilingual
- [x] Date picker allows viewing historical dates

---

**Last Updated:** 2026-03-26
**Status:** ✅ Implemented in code
**Blockers:** Phase F1 must be complete (design tokens used in chart colours)  
**Depends on:** Backend Phase 4 (analytics) + Phase 6 (emotion model) ✅ Complete
