IF DB_ID(N'equipement_solaire') IS NULL
BEGIN
    CREATE DATABASE equipement_solaire;
END
GO
USE equipement_solaire;
GO
/*
Schema SQL Server - Scenarios 1, 2A et 2B
Projet: Consommation avec panneau solaire et batterie
*/

IF OBJECT_ID('dbo.ConfigurationPratique', 'U') IS NOT NULL DROP TABLE dbo.ConfigurationPratique;
IF OBJECT_ID('dbo.ConfigurationRendement', 'U') IS NOT NULL DROP TABLE dbo.ConfigurationRendement;
IF OBJECT_ID('dbo.EquipementEnergieCaracteristique', 'U') IS NOT NULL DROP TABLE dbo.EquipementEnergieCaracteristique;
IF OBJECT_ID('dbo.UtilisationDetail', 'U') IS NOT NULL DROP TABLE dbo.UtilisationDetail;
IF OBJECT_ID('dbo.EquipementEnergie', 'U') IS NOT NULL DROP TABLE dbo.EquipementEnergie;
IF OBJECT_ID('dbo.MaterielPuissance', 'U') IS NOT NULL DROP TABLE dbo.MaterielPuissance;
IF OBJECT_ID('dbo.Equipement', 'U') IS NOT NULL DROP TABLE dbo.Equipement;
IF OBJECT_ID('dbo.Tranche', 'U') IS NOT NULL DROP TABLE dbo.Tranche;
IF OBJECT_ID('dbo.Materiel', 'U') IS NOT NULL DROP TABLE dbo.Materiel;
GO

CREATE TABLE dbo.Materiel (
    id INT IDENTITY(1,1) PRIMARY KEY,
    libelle NVARCHAR(120) NOT NULL UNIQUE
);
GO

CREATE TABLE dbo.Tranche (
    id INT IDENTITY(1,1) PRIMARY KEY,
    libelle NVARCHAR(20) NOT NULL UNIQUE,
    HeureDebut TIME(0) NOT NULL,
    HeureFin TIME(0) NOT NULL,
    CONSTRAINT CK_Tranche_Libelle CHECK (libelle IN ('AM', 'Hariva', 'Alina')),
    CONSTRAINT CK_Tranche_Heure CHECK (HeureDebut <> HeureFin)
);
GO

CREATE TABLE dbo.Equipement (
    id INT IDENTITY(1,1) PRIMARY KEY,
    libelle NVARCHAR(120) NOT NULL UNIQUE,
    type NVARCHAR(10) NOT NULL,
    CONSTRAINT CK_Equipement_Type CHECK (LOWER(type) IN ('ps', 'btr', 'autre'))
);
GO

CREATE TABLE dbo.MaterielPuissance (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idMaterielle INT NOT NULL,
    puissance DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_MaterielPuissance_Materiel FOREIGN KEY (idMaterielle)
        REFERENCES dbo.Materiel(id),
    CONSTRAINT CK_MaterielPuissance_Positive CHECK (puissance > 0)
);
GO

CREATE TABLE dbo.EquipementEnergie (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idEquipement INT NOT NULL,
    grandeurEnergetique DECIMAL(14,4) NULL,
    type NVARCHAR(10) NOT NULL CONSTRAINT DF_EquipementEnergie_Type DEFAULT 'thrq',
    CONSTRAINT FK_EquipementEnergie_Equipement FOREIGN KEY (idEquipement)
        REFERENCES dbo.Equipement(id),
    CONSTRAINT CK_EquipementEnergie_Type CHECK (LOWER(type) IN ('thrq', 'prtq'))
);
GO

CREATE TABLE dbo.UtilisationDetail (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idMaterielPuissance INT NOT NULL,
    idTranche INT NOT NULL,
    HeureDebut TIME(0) NOT NULL,
    HeureFin TIME(0) NOT NULL,
    CONSTRAINT FK_UtilisationDetail_MaterielPuissance FOREIGN KEY (idMaterielPuissance)
        REFERENCES dbo.MaterielPuissance(id),
    CONSTRAINT FK_UtilisationDetail_Tranche FOREIGN KEY (idTranche)
        REFERENCES dbo.Tranche(id),
    CONSTRAINT CK_UtilisationDetail_Heure CHECK (HeureDebut <> HeureFin)
);
GO

CREATE TABLE dbo.ConfigurationRendement (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idTranche INT NOT NULL,
    idEquipementEnergie INT NOT NULL,
    taux DECIMAL(6,2) NOT NULL,
    CONSTRAINT FK_ConfigurationRendement_Tranche FOREIGN KEY (idTranche)
        REFERENCES dbo.Tranche(id),
    CONSTRAINT FK_ConfigurationRendement_EquipementEnergie FOREIGN KEY (idEquipementEnergie)
        REFERENCES dbo.EquipementEnergie(id),
    CONSTRAINT CK_ConfigurationRendement_Taux CHECK (taux > 0 AND taux <= 100)
);
GO

CREATE TABLE dbo.ConfigurationPratique (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idEquipementEnergie INT NOT NULL,
    taux DECIMAL(6,2) NOT NULL,
    CONSTRAINT FK_ConfigurationPratique_EquipementEnergie FOREIGN KEY (idEquipementEnergie)
        REFERENCES dbo.EquipementEnergie(id),
    CONSTRAINT UQ_ConfigurationPratique_EquipementEnergie UNIQUE (idEquipementEnergie),
    CONSTRAINT CK_ConfigurationPratique_Taux CHECK (taux > 0)
);
GO

CREATE TABLE dbo.EquipementEnergieCaracteristique (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idEquipementEnergie INT NOT NULL,
    energieUnitaire DECIMAL(14,4) NOT NULL,
    prixUnitaire DECIMAL(14,2) NOT NULL,
    CONSTRAINT FK_EquipementEnergieCaracteristique_EquipementEnergie FOREIGN KEY (idEquipementEnergie)
        REFERENCES dbo.EquipementEnergie(id),
    CONSTRAINT UQ_EquipementEnergieCaracteristique_EquipementEnergie UNIQUE (idEquipementEnergie),
    CONSTRAINT CK_EquipementEnergieCaracteristique_Energie CHECK (energieUnitaire > 0),
    CONSTRAINT CK_EquipementEnergieCaracteristique_Prix CHECK (prixUnitaire > 0)
 );
GO
