# configuration node

# first meeting:
## child info:
    1. gender[1]: keep; delete 
    2. algorithmAge[1]: keep; delete 
    3. EnrollData[1]: dummy value; delete; keep
    4. ChildID[1]: keep; dummy value
    5. childKey[1]: keep; dummy value
    6. DOB[1]: delete; keep; dummy value

## Recording Info:
    1. UTCTime[1]: delete
    2. SerialNumber[1]: keep; delete
    3. TimeZone[1]: delete; keep
    1. LocalTime[1]: delete year, month, day keep time, add day of week; keep 
    4. ClockTime: delete year, month, day keep time, add day of week; keep; dummy value

# second meeting:
## Group 1(identity): make sure your ID information cannot be used to identify the individuals. 
    - childID
    - childKey
    - SerialNumber
## Group 2(Time): age info can sometimes be used to track individuals especially when paired with dates of recording DOB, please ensure that your combination of selections respects your ethics and consent requirement.
    - EnrollData->delete
    - DOB->set it to January 1, 1000
    - TimeZone->delete
    - UTC->delete
    - LocalTime->leave time of day alone, set date to based on new DOB
    - ClockTime->leave time of day alone, set date to based on new DOB

# all configurations:
./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime,LocalTime,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime,TimeZone,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime,UTCTime,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo,SerialNumber,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild,ChildKey,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild,DOB,1, 
./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild,Gender,1, 
./ChildInfo, algorithmAge, 1,  
./ChildInfo, gender, 1,  
./Recording, startClockTime, 1,  
./Recording, endClockTime, 1,  
./Bar, startClockTime, 1,  
./Bar/Recording, startClockTime, 1,  
./Bar/Recording, endClockTime, 1,  
./Bar/Recording/FiveMinuteSection, startClockTime, 1,  
./Bar/Recording/FiveMinuteSection, endClockTime, 1,  
./ExportData/Child, id, 1,  
./ExportData/Child, EnrollDate, 1,  
./ExportData/Child, ChildKey, 1,  
./ExportData/Child, DOB, 1,  
./ExportData/Child, Gender, 1,  

# note:
NOTE: This program takes all the .its files from a folder and removes information that might be used to identify the child, based on the user's selections.  It will generate a new folder that ends with "processed" at the place where the original folder is. It will also creates a report file that lists the old and new information for any fields that have been deleted or altered. Deletion of some information may prevent ADEX from functioning properly. It is the individual researcher's responsibility to ensure that any potentially identifying information is removed. This is very dependent on the individual lab's identity shielding practices, consent forms, ethics board and institutional policy, and laws of individual countries. Please leave in as much information as possible, but remember that information from one source could be combined downstream with another source to determine identities, so consider what other information may be found in other publicly available meta-data and derivative data. Save the original file, and a means of connecting the original with the anonymized file somewhere separate from the anonymized file. (I understand)
