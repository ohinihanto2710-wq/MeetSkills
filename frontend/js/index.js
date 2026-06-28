document.addEventListener('DOMContentLoaded', async () => {
  if (!isLoggedIn()) return;

  const container = document.getElementById('suggestionsCards');
  const matches = await getMatches();

  if (!matches || matches.length === 0) {
    container.innerHTML = '<p class="loading">Aucune suggestion pour le moment. Publiez une annonce !</p>';
    return;
  }

  container.innerHTML = matches.map(match => {
    const autre = match.annonce_offre.auteur === parseInt(localStorage.getItem('user_id'))
      ? match.annonce_demande : match.annonce_offre;
    const initiales = autre.auteur_nom.split(' ').map(n => n[0]).join('');
    const competences = match.competences_communes.map(c =>
      `<span class="badge badge--green">${c.nom}</span>`
    ).join('');

    return `
      <div class="card">
        <div class="card__header">
          <div class="avatar">${initiales}</div>
          <div>
            <div class="card__name">${autre.auteur_nom}</div>
            <div class="card__sub">${autre.domaine_etudes}</div>
          </div>
        </div>
        ${competences}
        <div class="card__score">${match.score}%</div>
        <div class="card__score-label">compatibilité</div>
      </div>
    `;
  }).join('');
});