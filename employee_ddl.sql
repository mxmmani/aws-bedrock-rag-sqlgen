-- Database
CREATE DATABASE employeedb;
--
-- Name: EmployeeAbsence; Type: TABLE; Schema: public; Owner: employeedb; Tablespace:
--
CREATE TABLE EmployeeAbsence 
(
 EmployeeID INT,
 EmployeeName NVARCHAR(255),
 AbsenceCode INT,
 AbsenceName NVARCHAR(255),
 Duration INT,
 StartDate DATE
);
