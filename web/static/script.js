

let distanceChart;

// ⚙ יצירת גרף מרחק בזמן (Chart.js)
function initChart() {
  const ctx = document.getElementById('distanceChart').getContext('2d');
  const data = {
    labels: [],
    datasets: [{
      label: 'מרחק (ס״מ)',
      data: [],
      borderColor: '#00f0ff',
      backgroundColor: 'rgba(0,240,255,0.2)',
      fill: true,
      tension: 0.3
    }]
  };

  const options = {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        suggestedMax: 200
      }
    },
    plugins: {
      legend: {
        labels: {
          color: '#00f0ff'
        }
      }
    }
  };

  distanceChart = new Chart(ctx, {
    type: 'line',
    data: data,
    options: options
  });
}

// 📡 קריאת נתונים מהשרת ועדכון DOM
function fetchSensorData() {
  fetch('/sensor_data')
    .then(response => response.json())
    .then(data => {
      const { distance, people_count } = data;
      updateValue('distance', distance);
      updateValue('people_count', people_count);
      updateAlerts(distance, people_count);
      updateGraph(distance);

      // שליחת נתוני החיישן ל-Firestore
      sendSensorDataToFirestore(distance, people_count);
    })
    .catch(err => console.error('Error fetching sensor data:', err));
}



// 🚨 עדכון אזור ההתראות
function updateAlerts(distance, peopleCount) {
  const alertsBox = document.getElementById('alerts-box');
  alertsBox.innerHTML = '';

  if (peopleCount > 5) {
    alertsBox.innerHTML += '<p class="alert alert-danger">⚠ עומס: יותר מ-5 אנשים!</p>';
  }
  if (distance < 30) {
    alertsBox.innerHTML += '<p class="alert alert-warning">⚠ מרחק נמוך מדי!</p>';
  }
}

// 📈 עדכון הגרף עם ערך חדש
function updateGraph(distance) {
  const label = new Date().toLocaleTimeString();
  const chart = distanceChart;
  const data = chart.data;

  data.labels.push(label);
  data.datasets[0].data.push(distance);

  if (data.labels.length > 20) {
    data.labels.shift();
    data.datasets[0].data.shift();
  }

  chart.update();
}

// ✏️ עדכון ערכים עם אפקט חזותי
function updateValue(id, newValue) {
  const el = document.getElementById(id);
  if (!el) return;

  if (el.textContent !== String(newValue)) {
    el.textContent = newValue;
    el.classList.add('updated');
    setTimeout(() => el.classList.remove('updated'), 1000);
  }
}

// ⏺ הקלטת וידאו – התחלה/עצירה
let isRecording = false;

function toggleRecording() {
    if (!isRecording) {
        // התחלת הקלטה
        fetch('/start_recording')

            .then(response => response.json())
            .then(data => {
                console.log("הקלטה התחילה", data);
                document.getElementById("record-btn").innerHTML = "⏹ עצור הקלטה";
                document.getElementById("recording-dot").style.display = "block";
                isRecording = true;
            })
            .catch(err => console.error(err));
    } else {
        // עצירת הקלטה
        fetch('/stop_recording')
            .then(response => response.json())
            .then(data => {
                console.log("הקלטה הופסקה", data);
                document.getElementById("record-btn").innerHTML = "📹 התחל הקלטה";
                document.getElementById("recording-dot").style.display = "none";
                isRecording = false;
            })
            .catch(err => console.error(err));
    }
}

// הנחה: יש לך משתנה db שמכיל את הפניה ל-Firestore (מהאתחול ב-HTML)
function sendSensorDataToFirestore(distance, peopleCount) {
  db.collection("sensor_data").add({
    timestamp: new Date(),
    distance: distance,
    people_count: peopleCount
  })
  .then(() => {
    console.log("נתוני חיישן נשמרו ב-Firestore!");
  })
  .catch((error) => {
    console.error("שגיאה בשמירת נתונים ל-Firestore: ", error);
  });
}


 // 📸 שמירת תמונת פריים
function saveFrame() {
  fetch('/save_frame', { method: 'POST' })
    .then(res => res.json())
    .then(data => alert(data.message));
}

// 📦 הורדת כל הקבצים ב-ZIP
function downloadAll() {
  window.location.href = '/download_all';
}

// 📁 טען רשימת קבצים, הצג עם כפתור מחיקה
function loadCaptures() {
  fetch('/list_captures')
    .then(response => response.json())
    .then(data => {
      const container = document.getElementById('captures-list');
      container.innerHTML = '';

      data.files.forEach(file => {
        const div = document.createElement('div');
        div.className = 'file-item';

        const link = document.createElement('a');
        link.href = `/download/${file}`;
        link.textContent = file;
        link.className = 'download-link';

        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '🗑';
        deleteBtn.className = 'delete-btn';
        deleteBtn.onclick = () => {
          fetch(`/delete_capture/${file}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(result => {
              alert(result.message);
              loadCaptures();
            });
        };

        div.appendChild(link);
        div.appendChild(deleteBtn);
        container.appendChild(div);
      });
    });
}

// 🚀 התחלה אוטומטית בהעלאת הדף
window.addEventListener('DOMContentLoaded', () => {
  initChart();
  fetchSensorData();
  loadCaptures();

  setInterval(fetchSensorData, 2000);
  setInterval(loadCaptures, 5000);
});

