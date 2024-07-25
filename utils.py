curriculum_data = {
  "First Year": {
    "Premier Semestre": [
      "Anatomie I",
      "Biologie Genetique",
      "Biochimie",
      "Communication et Langue",
      "Santé Publique",
      "Methodologie D'apprentissage"
    ],
    "Deuxieme Semestre": [
      "Anatomie II",
      "Biophysique",
      "Histologie / Embryologie",
      "Histoire de la Medecine / Psychosoc",
      "Technique de communication"
    ]
  },
  # ... (include all years and semesters as in your provided data)
}

schools_data = {
  "private": [
    "UIR",
    "Sheikh Zayed",
    "UMP6",
    "Sheikh Khalifa"
  ],
  "public": [
    "UIR Rabat",
    "Sheikh Zayed Casablanca",
    "UMP6 Tanger",
    "Sheikh Khalifa Oujda",
    "Fes",
    "Marrakech",
    "Agadir"
  ]
}

def generate_unique_id(school, topic, year):
    return f"{school}_{topic}_{year}".replace(" ", "_")