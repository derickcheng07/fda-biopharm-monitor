

|Target Field Name|Var Type|Source JSON Path|Use Case|
|-|-|-|-|
|saftery\_report\_id|VARCHAR(50)|safteryreportid|Identify submission and check for repeats.|
|receive\_date|DATE|receivedate|Used to parse YYYMMDD format to ISO.|
|patient\_age\_yrs|FLOAT|patient.patientonsetage, patient.patientonsetageunite|Use to identify and normalize patient age.|
|patient\_sex|VARCHAR(10)|patient.patientsex|Identify patient sex.|
|is\_serious|BOOLEAN|serious|True/false statement.|
|drug\_role|VARCHAR(20)|patient.drug\[].drugcharacterization|Raw string cleaned.|
|reported\_drug\_name|VARCHAR(100)|patient.drug\[].medicinalproduct||
|standard\_generic|VARCHAR(100)|patient.drug\[].openfda.generic\_name\[0]||
|adverse\_event\_pt|VARCHAR(150)|patient.reaction\[].reactionmeddrapt||



