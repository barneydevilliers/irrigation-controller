-- MySQL dump 10.13  Distrib 5.6.24, for debian-linux-gnu (x86_64)
--
-- Host: farmserver    Database: irrigation
-- ------------------------------------------------------
-- Server version	5.5.31-0+wheezy1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `programs`
--

DROP TABLE IF EXISTS `programs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `programs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `programs`
--

LOCK TABLES `programs` WRITE;
/*!40000 ALTER TABLE `programs` DISABLE KEYS */;
INSERT INTO `programs` VALUES (1,'Odd Days Morning Program'),(2,'Even Days Morning Program'),(3,'Midday Nursery Program'),(4,'Test Program');
/*!40000 ALTER TABLE `programs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `programsequence`
--

DROP TABLE IF EXISTS `programsequence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `programsequence` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `programid` int(11) NOT NULL,
  `valveid` int(11) NOT NULL,
  `sequenceorder` int(11) NOT NULL DEFAULT '0',
  `runtime` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `programsequence`
--

LOCK TABLES `programsequence` WRITE;
/*!40000 ALTER TABLE `programsequence` DISABLE KEYS */;
INSERT INTO `programsequence` VALUES (1,1,1,1,40),(2,1,3,2,10),(3,1,4,3,10),(4,1,5,4,5),(5,2,1,1,5),(6,2,2,2,30),(7,2,3,3,10),(8,2,4,4,10),(9,2,5,5,5),(10,3,4,1,5),(11,4,2,1,1),(12,4,3,2,2),(13,4,4,3,1);
/*!40000 ALTER TABLE `programsequence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `starts`
--

DROP TABLE IF EXISTS `starts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `starts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `programid` int(11) DEFAULT NULL,
  `timeofday` varchar(45) DEFAULT NULL,
  `days` varchar(4) NOT NULL DEFAULT 'ALL',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `starts`
--

LOCK TABLES `starts` WRITE;
/*!40000 ALTER TABLE `starts` DISABLE KEYS */;
INSERT INTO `starts` VALUES (1,1,'06:00','odd'),(2,2,'06:00','even'),(3,3,'12:00','all'),(4,4,'10:15','all');
/*!40000 ALTER TABLE `starts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `valvedependencies`
--

DROP TABLE IF EXISTS `valvedependencies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `valvedependencies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `valveid` int(11) NOT NULL,
  `dependonvalveid` int(11) NOT NULL,
  PRIMARY KEY (`id`,`valveid`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `valvedependencies`
--

LOCK TABLES `valvedependencies` WRITE;
/*!40000 ALTER TABLE `valvedependencies` DISABLE KEYS */;
INSERT INTO `valvedependencies` VALUES (1,1,6),(2,2,6),(3,3,6),(4,4,6),(5,5,6);
/*!40000 ALTER TABLE `valvedependencies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `valves`
--

DROP TABLE IF EXISTS `valves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `valves` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(45) DEFAULT NULL,
  `interface` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `valves`
--

LOCK TABLES `valves` WRITE;
/*!40000 ALTER TABLE `valves` DISABLE KEYS */;
INSERT INTO `valves` VALUES (1,'Vegetable Garden','1'),(2,'Backyard','2'),(3,'Frontyard','3'),(4,'Greenhouse','4'),(5,'Watertank','5');
/*!40000 ALTER TABLE `valves` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-11-15 10:19:15
