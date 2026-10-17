import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

function toRows(etudiants) {
  return etudiants.map(s => ({
    Code: s.code,
    Numero: s.numero,
    Nom: s.nom,
    Prenom: s.prenom,
    Classe: s.classe,
    Moyenne: s.moyenne_generale ?? '-',
    Provenance: s.provenance
  }))
}

export function exportToExcel(etudiants, filename = 'etudiants.xlsx') {
  const rows = toRows(etudiants)
  const worksheet = XLSX.utils.json_to_sheet(rows)
  worksheet['!cols'] = [
    { wch: 10 }, { wch: 14 }, { wch: 18 }, { wch: 18 }, { wch: 10 }, { wch: 10 }, { wch: 12 }
  ]
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Étudiants')
  XLSX.writeFile(workbook, filename)
}

export function exportToPdf(etudiants, filename = 'etudiants.pdf') {
  const doc = new jsPDF()
  doc.setFontSize(14)
  doc.setTextColor(44, 62, 80)
  doc.text('Liste des Étudiants', 14, 16)
  doc.setFontSize(9)
  doc.setTextColor(100, 116, 139)
  doc.text(`Généré le ${new Date().toLocaleDateString('fr-FR')}`, 14, 22)

  const rows = toRows(etudiants)
  autoTable(doc, {
    startY: 28,
    head: [['Code', 'Numéro', 'Nom', 'Prénom', 'Classe', 'Moyenne', 'Provenance']],
    body: rows.map(r => Object.values(r)),
    headStyles: { fillColor: [44, 62, 80] },
    styles: { fontSize: 9 },
    alternateRowStyles: { fillColor: [248, 250, 252] }
  })

  doc.save(filename)
}

// Bulletin individuel d'un étudiant (fiche détaillée → PDF)
export function exportBulletinPdf({ student, notes, average, mention, appreciation, rank, classSize, classAverage, birthLabel, labels }) {
  const doc = new jsPDF()
  const fullName = `${student.prenom} ${student.nom}`

  // Bandeau d'en-tête
  doc.setFillColor(12, 58, 64)
  doc.rect(0, 0, 210, 36, 'F')
  doc.setFillColor(242, 169, 59)
  doc.rect(0, 36, 210, 2, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(18)
  doc.text(labels.title, 14, 20)
  doc.setFontSize(11)
  doc.setTextColor(180, 207, 209)
  doc.text(fullName, 14, 29)

  // Identité
  doc.setTextColor(16, 37, 45)
  doc.setFontSize(12)
  doc.text(labels.id, 14, 52)
  doc.setFontSize(10)
  doc.setTextColor(56, 80, 88)
  const identity = [
    [labels.code, student.code],
    [labels.numero, student.numero],
    [labels.classe, student.classe],
    [labels.birth, birthLabel]
  ]
  identity.forEach(([label, value], i) => {
    const y = 60 + i * 7
    doc.setTextColor(102, 125, 134)
    doc.text(`${label}`, 14, y)
    doc.setTextColor(16, 37, 45)
    doc.text(`${value ?? '-'}`, 52, y)
  })

  // Résultats par matière
  autoTable(doc, {
    startY: 94,
    head: [[labels.subject, labels.homework, labels.exam, labels.average]],
    body: notes.map(n => [
      n.matiere,
      n.devoirs.join(' ; ') || '-',
      n.examen.toFixed(2),
      n.moyenne.toFixed(2)
    ]),
    headStyles: { fillColor: [15, 107, 102] },
    styles: { fontSize: 10 },
    alternateRowStyles: { fillColor: [246, 249, 249] },
    columnStyles: { 2: { halign: 'center' }, 3: { halign: 'center', fontStyle: 'bold' } }
  })

  // Synthèse
  let y = doc.lastAutoTable.finalY + 14
  doc.setFontSize(12)
  doc.setTextColor(16, 37, 45)
  doc.text(`${labels.general} : ${average.toFixed(2)} / 20  (${mention})`, 14, y)
  y += 8
  doc.setFontSize(10)
  doc.setTextColor(56, 80, 88)
  if (rank) { doc.text(`${labels.rank} : ${rank} / ${classSize}`, 14, y); y += 6 }
  if (classAverage) { doc.text(`${labels.classAvg} : ${classAverage.toFixed(2)}`, 14, y); y += 8 }
  doc.splitTextToSize(appreciation, 180).forEach(line => { doc.text(line, 14, y); y += 5 })

  // Pied de page
  doc.setFontSize(8)
  doc.setTextColor(120, 135, 140)
  doc.text(`${labels.generated} ${new Date().toLocaleDateString('fr-FR')}`, 14, 288)

  doc.save(`bulletin-${student.numero}.pdf`)
}
