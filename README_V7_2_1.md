# v7.2.1 — Mémoire automatique des emplois du temps

Dès qu'un emploi est uploadé et extrait :

- premier contenu → V1 ;
- même contenu uploadé de nouveau → aucun doublon ;
- contenu différent pour la même année / période / filière / semestre → V2, puis V3... ;
- la nouvelle version devient active ;
- l'ancienne reste archivée ;
- la base `estn.db` est synchronisée vers Google Drive.

La période est déduite automatiquement du semestre :
- S1 / S3 / S5 → Automne
- S2 / S4 / S6 → Printemps

Si année universitaire, filière ou semestre manque, l'application n'invente rien :
elle affiche un avertissement et ne mémorise pas encore cet emploi.
