const semanaCtx = document.getElementById('semanaChart')

const semanaChart = new Chart(semanaCtx, {
  type: 'bar',
  data: {
    labels: JSON.parse(semanaCtx.getAttribute('data-labels')),
    datasets: [{
      label: 'Ingresos',
      data: JSON.parse(semanaCtx.getAttribute('data-data')),
      backgroundColor: 'rgba(54, 162, 235, 0.5)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1
    }]
  },
  options: {
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
})