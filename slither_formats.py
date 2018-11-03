# Automatic floppy disk format generator.

formats = {}
table = {"OEM_Label": "",
         "Bytes_Per_Sector": 0,
         "Sectors_Per_Cluster" : 0,
         "Reserved_Sectors": 0,
         "FATs": 0,
         "Dir_Entries": 0,
         "Logical_Sectors": 0,
         "Media_ID": 0,
         "Sectors_Per_FAT": 0,
         "Sectors_Per_Track": 0,
         "Sides": 0,
         "Hidden_Sectors": 0,
         "LBA_Sectors": 0,
         "Drive_Number": 0,
         "Windows_NT_Flag": 0,
         "Signature": 0,
         "Volume_ID": 0,
         "Volume_Label": "",
         "Identifier": ""}

def add_format(n):
    formats[n] = table.copy()
    

def build_formats():
    content = ""

    for i in formats:
        if content:
            content += "\n"

        content += "[%s]\n\n" % i
        content += "OEM_Label = %s\n" % formats[i]["OEM_Label"]
        content += "Bytes_Per_Sector = %d\n" % formats[i]["Bytes_Per_Sector"]
        content += "Sectors_Per_Cluster = %d\n" % formats[i]["Sectors_Per_Cluster"]
        content += "Reserved_Sectors = %d\n" % formats[i]["Reserved_Sectors"]
        content += "FATs = %d\n" % formats[i]["FATs"]
        content += "Dir_Entries = %d\n" % formats[i]["Dir_Entries"]
        content += "Logical_Sectors = %d\n" % formats[i]["Logical_Sectors"]
        content += "Media_ID = %d\n" % formats[i]["Media_ID"]
        content += "Sectors_Per_FAT = %d\n" % formats[i]["Sectors_Per_FAT"]
        content += "Sectors_Per_Track = %d\n" % formats[i]["Sectors_Per_Track"]
        content += "Sides = %d\n" % formats[i]["Sides"]
        content += "Hidden_Sectors = %d\n" % formats[i]["Hidden_Sectors"]
        content += "LBA_Sectors = %d\n" % formats[i]["LBA_Sectors"]
        content += "Drive_Number = %d\n" % formats[i]["Drive_Number"]
        content += "Windows_NT_Flag = %d\n" % formats[i]["Windows_NT_Flag"]
        content += "Signature = %d\n" % formats[i]["Signature"]
        content += "Volume_ID = %d\n" % formats[i]["Volume_ID"]
        content += "Volume_Label = %s\n" % formats[i]["Volume_Label"]
        content += "Identifier = %s\n" % formats[i]["Identifier"]

    f = open("formats.ini", "w")
    f.write(content)
    f.close()

if __name__ == "__main__":
    # Setup the first format.
    table["OEM_Label"] = ""
    table["Bytes_Per_Sector"] = 512
    table["Sectors_Per_Cluster"] = 1
    table["Reserved_Sectors"] = 1
    table["FATs"] = 2
    table["Dir_Entries"] = 244
    table["Logical_Sectors"] = 640
    table["Media_ID"] = 240
    table["Sectors_Per_FAT"] = 9
    table["Sectors_Per_Track"] = 8
    table["Sides"] = 1
    table["Hidden_Sectors"] = 0
    table["LBA_Sectors"] = 0
    table["Drive_Number"] = 0
    table["Windows_NT_Flag"] = 0
    table["Signature"] = 41
    table["Volume_ID"] = 0
    table["Volume_Label"] = ""
    table["Identifier"] = "FAT12"
    add_format("IBM PC 3.5IN 320KB")

    table["Logical_Sectors"] = 720
    table["Sectors_Per_Track"] = 9
    add_format("IBM PC 3.5IN 360KB")

    table["Logical_Sectors"] = 1280
    table["Sectors_Per_Track"] = 8
    table["Sides"] = 2
    add_format("IBM PC 3.5IN 640KB")

    table["Logical_Sectors"] = 1440
    table["Sectors_Per_Track"] = 9
    add_format("IBM PC 3.5IN 720KB")

    table["Logical_Sectors"] = 2880
    table["Sectors_Per_Track"] = 18
    add_format("IBM PC 3.5IN 1.44MB")

    table["Logical_Sectors"] = 3360
    table["Sectors_Per_Track"] = 21
    add_format("IBM PC 3.5IN 1.68MB")

    table["Logical_Sectors"] = 3444
    add_format("IBM PC 3.5IN 1.72MB")

    table["Logical_Sectors"] = 5760
    table["Sectors_Per_Track"] = 36
    add_format("IBM PC 3.5IN 2.88MB")

    build_formats()
