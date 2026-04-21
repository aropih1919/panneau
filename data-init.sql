/*
Jeu de donnees de test - Scenarios 1, 2A et 2B
*/

/*
Nettoyage des donnees existantes et reinitialisation des IDENTITY.
L'ordre respecte les cles etrangeres pour SQL Server.
*/
DELETE FROM dbo.ConfigurationPratique;
DELETE FROM dbo.ConfigurationRendement;
DELETE FROM dbo.EquipementEnergieCaracteristique;
DELETE FROM dbo.UtilisationDetail;
DELETE FROM dbo.EquipementEnergie;
DELETE FROM dbo.MaterielPuissance;
DELETE FROM dbo.Equipement;
DELETE FROM dbo.Tranche;
DELETE FROM dbo.Materiel;

SELECT COUNT(*) AS nb_tranche FROM dbo.Tranche;
SELECT COUNT(*) AS nb_materiel FROM dbo.Materiel;

DBCC CHECKIDENT ('dbo.ConfigurationPratique', RESEED, 0);
DBCC CHECKIDENT ('dbo.ConfigurationRendement', RESEED, 0);
DBCC CHECKIDENT ('dbo.EquipementEnergieCaracteristique', RESEED, 0);
DBCC CHECKIDENT ('dbo.UtilisationDetail', RESEED, 0);
DBCC CHECKIDENT ('dbo.EquipementEnergie', RESEED, 0);
DBCC CHECKIDENT ('dbo.MaterielPuissance', RESEED, 0);
DBCC CHECKIDENT ('dbo.Equipement', RESEED, 0);
DBCC CHECKIDENT ('dbo.Tranche', RESEED, 0);
DBCC CHECKIDENT ('dbo.Materiel', RESEED, 0);
GO

/*
Tranches visibles dans l'interface.
*/
INSERT INTO dbo.Tranche (libelle, HeureDebut, HeureFin)
VALUES
    ('AM', '06:00:00', '16:59:00'),
    ('Hariva', '17:00:00', '18:59:00'),
    ('Alina', '19:00:00', '05:59:00');
GO

/*
Equipements de base du projet.
*/
INSERT INTO dbo.Equipement (libelle, type)
VALUES
    ('Panneau', 'ps'),
    ('Batterie', 'btr'),
    ('Convertisseur', 'autre');
GO

/*
Chaque panneau dispose de sa propre ligne EquipementEnergie avec ses
caracteristiques specifiques (energieUnitaire, prixUnitaire).
*/
INSERT INTO dbo.EquipementEnergie (idEquipement, grandeurEnergetique, type)
SELECT e.id, NULL, 'thrq'
FROM dbo.Equipement e
JOIN (
    VALUES
        ('Panneau'),
        ('Panneau'),
        ('Panneau'),
        ('Batterie'),
        ('Convertisseur')
) AS v(libelle)
    ON v.libelle = e.libelle;
GO

INSERT INTO dbo.EquipementEnergieCaracteristique (idEquipementEnergie, energieUnitaire, prixUnitaire)
SELECT
    ee.id,
    v.energieUnitaire,
    v.prixUnitaire
FROM (
    SELECT
        ee.id,
        e.libelle,
        ROW_NUMBER() OVER (PARTITION BY e.libelle ORDER BY ee.id) AS rang
    FROM dbo.EquipementEnergie ee
    JOIN dbo.Equipement e
        ON e.id = ee.idEquipement
) AS ee
JOIN (
    VALUES
        ('Panneau', 1, 100.00, 250000.00),
        ('Panneau', 2, 150.00, 320000.00),
        ('Panneau', 3, 200.00, 410000.00),
        ('Batterie', 1, 1200.00, 600000.00),
        ('Convertisseur', 1, 500.00, 150000.00)
) AS v(libelle, rang, energieUnitaire, prixUnitaire)
    ON v.libelle = ee.libelle
   AND v.rang = ee.rang;
GO

/*
Materiels saisis dans la capture.
*/
INSERT INTO dbo.Materiel (libelle)
VALUES
    ('Lampe 10W'),
    ('Frigo 120W'),
    ('TV 55W'),
    ('Wifi 10W'),
    ('Ventilo 75W');
GO

/*
Puissance de chaque materiel.
Une seule puissance par materiel dans cet exemple.
*/
INSERT INTO dbo.MaterielPuissance (idMaterielle, puissance)
SELECT m.id, v.puissance
FROM dbo.Materiel m
JOIN (
    VALUES
        ('Lampe 10W', 10.00),
        ('Frigo 120W', 120.00),
        ('TV 55W', 55.00),
        ('Wifi 10W', 10.00),
        ('Ventilo 75W', 75.00)
) AS v(libelle, puissance)
    ON v.libelle = m.libelle;
GO

/*
Details d'utilisation correspondant aux lignes de la capture.
*/
INSERT INTO dbo.UtilisationDetail (idMaterielPuissance, idTranche, HeureDebut, HeureFin)
SELECT mp.id, t.id, v.heure_debut, v.heure_fin
FROM (
    VALUES
        ('Lampe 10W', 'Alina',  '19:00:00', '23:00:00'),
        ('Frigo 120W', 'Alina', '19:00:00', '06:00:00'),
        ('TV 55W', 'Hariva',    '17:00:00', '19:00:00'),
        ('Wifi 10W', 'Alina',   '19:00:00', '06:00:00'),
        ('Lampe 10W', 'Hariva', '17:00:00', '19:00:00'),
        ('Ventilo 75W', 'AM',   '10:00:00', '14:00:00'),
        ('TV 55W', 'AM',        '08:00:00', '12:00:00'),
        ('Frigo 120W', 'AM',    '06:00:00', '17:00:00')
) AS v(libelle_materiel, libelle_tranche, heure_debut, heure_fin)
JOIN dbo.Materiel m
    ON m.libelle = v.libelle_materiel
JOIN dbo.MaterielPuissance mp
    ON mp.idMaterielle = m.id
JOIN dbo.Tranche t
    ON t.libelle = v.libelle_tranche;
GO
 veuillez modifier pour que dans l affichage des ETU, il y a mon numero ETU0042
