---
--- drop tables
---
DROP TABLE [dbo].[EmployeeAbsence];
--
-- Name: EmployeeAbsence; Type: TABLE; Schema: public; Owner: -; Tablespace:
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
