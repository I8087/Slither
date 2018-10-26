# Floppy Disk Manipulation Tool
# Slither

import os
import configparser

    #"IBM PC 3.5IN 320KB"
    #"IBM PC 3.5IN 360KB"
    #"IBM PC 3.5IN 640KB"
    #"IBM PC 3.5IN 720KB"
    #"IBM PC 3.5IN 1.44MB"
    #"IBM PC 3.5IN 1.68MB"
    #"IBM PC 3.5IN 1.72MB"
    #"IBM PC 3.5IN 2.88MB"


KiB = 1024
MiB = KiB * 1024
Sector = 512

class FAT12:

    def __init__(self, f=""):

        self.disk_formats = {}

        self.fp = f

        self.f = None

        self.FS = "FAT12"

        self.attr = {
            "OEM_Label" : "",
            "Bytes_Per_Sector" : 0,
            "Sectors_Per_Cluster" : 0,
            "Reserved_Sectors" : 0,
            "FATs" : 0,
            "Dir_Entries" : 0,
            "Logical_Sectors" : 0,
            "Media_ID" : 0,
            "Sectors_Per_FAT" : 0,
            "Sectors_Per_Track" : 0,
            "Sides": 0,
            "Hidden_Sectors": 0,
            "LBA_Sectors": 0,
            "Drive_Number": 0,
            "Windows_NT_Flag": 0,
            "Signature": 0,
            "Volume_ID": 0,
            "Volume_Label": "",
            "Identifier": ""}

        self.get_disk_formats()

    # Get a list of disk formats from formats.ini
    def get_disk_formats(self):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read("formats.ini")
        for i in config.sections():
            self.disk_formats[i] = {}
            for x in config[i]:
                if x in ("OEM_Label", "Volume_Label", "Identifier"):
                    self.disk_formats[i][x] = str(config[i][x])
                else:
                    self.disk_formats[i][x] = int(config[i][x])

    def mount(self, file=""):
        if file:
            self.fp = file
        else:
            file = self.fp

        if os.path.exists(file):
            self.f = open(file, "rb+")
            self.f.seek(3)

            # BPB
            self.attr["OEM_Label"] = self.f.read(8).decode(encoding="ascii").rstrip()
            self.attr["Bytes_Per_Sector"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Sectors_Per_Cluster"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Reserved_Sectors"] = int.from_bytes(self.f.read(2), "little")
            self.attr["FATs"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Dir_Entries"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Logical_Sectors"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Media_ID"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Sectors_Per_FAT"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Sectors_Per_Track"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Sides"] = int.from_bytes(self.f.read(2), "little")
            self.attr["Hidden_Sectors"] = int.from_bytes(self.f.read(4), "little")
            self.attr["LBA_Sectors"] = int.from_bytes(self.f.read(4), "little")

            # EPBP
            self.attr["Drive_Number"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Windows_NT_Flag"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Signature"] = int.from_bytes(self.f.read(1), "little")
            self.attr["Volume_ID"] = int.from_bytes(self.f.read(4), "little")
            self.attr["Volume_Label"] = self.f.read(11).decode(encoding="ascii").rstrip()
            self.attr["Identifier"] = self.f.read(8).decode(encoding="ascii").rstrip()

            return True

        return False

    def unmount(self):
        if self.f:
            self.f.close()
            self.f = None
            return True

        return False

    # Check to see if we're mounted.
    def isMounted(self):
        if self.f:
            return True
        else:
            return False

    def getDirSector(self):
        return (self.attr["Dir_Entries"] *32) // self.attr["Bytes_Per_Sector"]

    def getFirstDataSector(self):
        return self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"] + self.getDirSector()    

    def format(self, style):
            if not style in self.disk_formats:
                exit(-1)

            self.attr = self.disk_formats[style]

            self.f = open(self.fp, "wb")

          # Number of logical sectors multiplied by bytes per sector.
            for i in range(self.attr["Logical_Sectors"] * self.attr["Bytes_Per_Sector"]):
                self.f.write(b'\x00')
            self.f.close()

            self.f = open(self.fp, "rb+")

            #BPB
            self.f.seek(0)
            self.f.write(b'\xEB\x3C\x90')
            self.f.write(bytes(self.attr["OEM_Label"][:8].ljust(8), "ascii"))
            self.f.write(self.attr["Bytes_Per_Sector"].to_bytes(2, "little"))
            self.f.write(self.attr["Sectors_Per_Cluster"].to_bytes(1, "little"))
            self.f.write(self.attr["Reserved_Sectors"].to_bytes(2, "little"))
            self.f.write(self.attr["FATs"].to_bytes(1, "little"))
            self.f.write(self.attr["Dir_Entries"].to_bytes(2, "little")) # Directory Entries
            self.f.write(self.attr["Logical_Sectors"].to_bytes(2, "little")) # Logical sectors
            self.f.write(self.attr["Media_ID"].to_bytes(1, "little")) # Media Descriptor
            self.f.write(self.attr["Sectors_Per_FAT"].to_bytes(2, "little")) # Sectors Per FAT
            self.f.write(self.attr["Sectors_Per_Track"].to_bytes(2, "little")) # Sectors Per Track
            self.f.write(self.attr["Sides"].to_bytes(2, "little")) # Number of Sides
            self.f.write(self.attr["Hidden_Sectors"].to_bytes(4, "little")) # Hidden Sectors
            self.f.write(self.attr["LBA_Sectors"].to_bytes(4, "little")) # LBA Sectors

            #EBPB
            self.f.write(self.attr["Drive_Number"].to_bytes(1, "little")) # Drive Number
            self.f.write(self.attr["Windows_NT_Flag"].to_bytes(1, "little")) # Windows NT Flag
            self.f.write(self.attr["Signature"].to_bytes(1, "little")) # Signature
            self.f.write(self.attr["Volume_ID"].to_bytes(4, "little")) # Volume ID
            self.f.write(bytes(self.attr["Volume_Label"][:11].ljust(11), "ascii")) # Volume Label
            self.f.write(bytes(self.attr["Identifier"][:8].ljust(8), "ascii")) # File System Identifier

            self.f.close()


    # Gets a list of Files on the Floppy.
    def getDir(self, vFAT=False):
        l = []
        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])
        name = b""
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)
            if not fn[0]:
                break
            elif fn[0] == 0xE5:
                pass
            elif vFAT and fn[11] == 0x0F:
                for i in range(5):
                    if fn[1+(i*2)].to_bytes(1, "little") not in (b'\x00', b'\xFF'):
                        name += fn[1+(i*2)].to_bytes(2, "little")
                for i in range(6):
                    if fn[0xE+(i*2)].to_bytes(1, "little") not in (b'\x00', b'\xFF'):
                        name += fn[0xE+(i*2)].to_bytes(2, "little")
                for i in range(2):
                    if fn[0x1C+(i*2)].to_bytes(1, "little") not in (b'\x00', b'\xFF'):
                        name += fn[0x1C+(i*2)].to_bytes(2, "little")
            elif name:
                l.append(name.decode(encoding="utf-16"))
                name = b""
            elif fn[11] != 0x0F:
                l.append(fn[:8].decode(encoding="ascii").rstrip() + "." + fn[8:11].decode(encoding="ascii").rstrip())

        return tuple(i for i in sorted(l))

    def getFile(self, file, vFAT=False):
        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)

            if fn[0] not in (0x00, 0xE5) and fn[11] != 0x0F:
                file2 = fn[:8].decode(encoding="ascii").rstrip() + "." + fn[8:11].decode(encoding="ascii").rstrip()
                if file == file2:

                    # Get cluster and file size.
                    cluster = int.from_bytes(fn[26:28], "little")
                    file_size = int.from_bytes(fn[28:32], "little")
                    contents = bytes()

                    while cluster and (cluster < 0xFF0) and (file_size > 1):

                        # Load the sector.
                        self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

                        # Check to see if this is the last sector.
                        if file_size > (self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]):
                            contents += self.f.read(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])
                        else:
                            contents += self.f.read(file_size)

                        # Subtract a sector from the file size counter.
                        file_size -= self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]

                        # Calculate the location of the next cluster.
                        fat_offset = cluster + (cluster // 2)

                        # Check if the current cluster is even or odd.
                        even = cluster & 1

                        # Load the next cluster.
                        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                        cluster = int.from_bytes(self.f.read(2), "little")

                        # Adjust the 12-bit cluster appropriately.
                        if even:
                            cluster >>= 4
                        else:
                            cluster &= 0x0FFF

                    return contents

        return False

    # Rename a file.
    def renameFile(self, oldname, newname):
        oldname = oldname.split(".")[0][:8].ljust(8).upper() + oldname.split(".")[1][:3].ljust(3).upper()
        newname = newname.split(".")[0][:8].ljust(8).upper() + newname.split(".")[1][:3].ljust(3).upper()

        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])
        # See if the new file name exists.
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)
            if fn[0] not in (0x00, 0xE5) and fn[11] != 0x0F:
                if fn[:11].decode(encoding="ascii") == newname:
                    return False

        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)
            if fn[0] not in (0x00, 0xE5) and fn[11] != 0x0F:
                if  fn[:11].decode(encoding="ascii") == oldname:
                    self.f.seek(-32, 1)
                    self.f.write(bytes(newname, "ascii"))
                    return True

        return False

    # Deletes a file if it exists.
    def deleteFile(self, file):
        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)
            if fn[0] not in (0x00, 0xE5) and fn[11] != 0x0F:
                file2 = fn[:8].decode(encoding="ascii").rstrip() + "." + fn[8:11].decode(encoding="ascii").rstrip()
                if file == file2:

                    # Save the first cluster.
                    cluster = int.from_bytes(fn[26:28], "little")

                    self.f.seek(-32, 1)

                    # Mark the entry as deleted and clear it out.
                    self.f.write(b'\xE5' + b'\x00'*31)

                    while cluster and (cluster < 0xFF0):

                        # Calculate the location of the next cluster.
                        fat_offset = cluster + (cluster // 2)

                        # Check if the current cluster is even or odd.
                        even = cluster & 1

                        # Load the next cluster.
                        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                        cluster = int.from_bytes(self.f.read(2), "little")
                        self.f.seek(-2, 1)

                        # Adjust the 12-bit cluster appropriately.
                        if even:
                            self.f.write((cluster & 0x000F).to_bytes(2, "little"))
                            cluster >>= 4
                        else:
                            self.f.write((cluster & 0xF000).to_bytes(2, "little"))
                            cluster &= 0x0FFF

                    return

    def saveFile(self, file, contents):
        # Remove the old file. We're overwriting it.
        self.deleteFile(file)

        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])

        # Find free entry space.
        for i in range(self.attr["Dir_Entries"]):
            fn = self.f.read(32)

            # Do if dir entry is free.
            if fn[0] ==0xE5 and fn[11] != 0x0F:
                file_size = len(contents)

                self.f.seek(-32, 1)

                ent_loc = self.f.tell()

                # Write the file name.
                self.f.write(bytes(file.split(".")[0][:8].ljust(8).upper(), "ascii"))
                self.f.write(bytes(file.split(".")[1][:3].ljust(3).upper(), "ascii"))
                self.f.write(b'\x00') # Attributes.
                self.f.write(b'\x00') # Windows NT Flag
                self.f.write(b'\x00') # Creation time in tenths of a second.
                self.f.write(b'\x00\x00') # Time
                self.f.write(b'\x00\x00') # Date
                self.f.write(b'\x00\x00') # Last Access Date.
                self.f.write(b'\x00\x00') # Higher 16-bit cluster.
                self.f.write(b'\x00\x00') # Last modified time
                self.f.write(b'\x00\x00') # Last modified date.
                self.f.write(b'\x00\x00') # Lower 16-bit cluster.
                self.f.write(file_size.to_bytes(4, "little")) # Size of file in bytes.

                # Find the number of clusters needed.
                sectors = file_size // self.attr["Bytes_Per_Sector"]

                # Fit the last data into the size of a sector, if needed.
                if file_size % self.attr["Bytes_Per_Sector"]:
                    contents += b'\x00' * (self.attr["Bytes_Per_Sector"] - (file_size % self.attr["Bytes_Per_Sector"]))
                    sectors += 1

                cluster = 0
                cluster_chain = []

                while sectors:

                    # Calculate the location of the next cluster.
                    fat_offset = cluster + (cluster // 2)

                    # Check if the current cluster is even or odd.
                    even = cluster & 1

                    # Check the next cluster.
                    self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                    _cluster = int.from_bytes(self.f.read(2), "little")

                    # Adjust the 12-bit cluster appropriately.
                    if even:
                        _cluster >>= 4
                    else:
                        _cluster &= 0x0FFF

                    if not _cluster:
                        cluster_chain.append(cluster)
                        sectors -= 1

                    cluster += 1

                cluster_chain.append(0x0FFF)
                last_cluster = 0

                for cluster in cluster_chain:

                    if cluster != 0xFFF:

                        # Load the sector.
                        self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

                        # Write to the sector.
                        self.f.write(contents[:self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]])
                        contents = contents[self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]:]


                    # Save the cluster in the chain.
                    if last_cluster:
                    
                        # Calculate the location of the next cluster.
                        fat_offset = last_cluster + (cluster // 2)

                        # Check if the current cluster is even or odd.
                        even = last_cluster & 1

                        # Load the next cluster.
                        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                        last_cluster = int.from_bytes(self.f.read(2), "little")

                        # Adjust the 12-bit cluster appropriately.
                        if even:
                            last_cluster = cluster + (last_cluster & 0xF000)
                        else:
                            cluster <<= 4
                            last_cluster = cluster + (last_cluster & 0x000F)

                        self.f.seek(-2, 1)
                        self.f.write(last_cluster.to_bytes(2, "little"))

                        last_cluster = cluster

                    else:
                        self.f.seek(ent_loc+26)
                        self.f.write(cluster.to_bytes(2, "little"))
                        last_cluster = cluster
                                     
                return True

        return False

if __name__ == "__main__":
    print("Not a standalone script!")
    exit(-1)
