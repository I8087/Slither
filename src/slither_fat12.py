# Floppy Disk Manipulation Tool
# Slither

import os
import configparser
import datetime

# Handles all of the IO exceptions in Slither.
class SlitherIOError(Exception):

    def __init__(self, value, msg):
        self.value = value
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

# The main library of FAT12 functions.
class FAT12:

    def __init__(self, f=""):

        # A dictionary containing common floppy disk file formats.
        self.disk_formats = {}

        self.fp = f

        self.f = None

        self.FS = "FAT12"

        # Current directory path.
        self.path = "./"

        # Start of the cluster chain for current directory.
        self.dir_cluster = 0

        # Flags for the attributes of a file entry.
        self.attr_flags = {"READ_ONLY": 0x01,
                            "HIDDEN": 0x02,
                            "SYSTEM": 0x04,
                            "VOLUME_ID": 0x08,
                            "DIRECTORY": 0x10,
                            "ARCHIVE": 0x20,
                            "LFN": 0x0F}

        # A dictionary for the BIOS Parameter Block.
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

    #######################
    # INTERNAL FUNCTIONS
    #######################

    # Seek the Root Directory.
    def _seek_root(self):
        self.f.seek((self.attr["Reserved_Sectors"]+self.attr["Sectors_Per_FAT"]*self.attr["FATs"])*self.attr["Bytes_Per_Sector"])

    # Seeks a file. Returns False if it doesn't exist, otherwise it's True.
    def _seek_file(self, file):

        # Get a list of files in the directory.
        e = self.getDir()
        e_files = [i for i in e if e[i]["IS_FILE"]]
        
        # Find the file!
        if file in e_files:
            self.f.seek(e[file]["LBA"])
            return True
        else:
            return False

    # Seeks a free entry.
    # Deprecated. Use findFreeEntry()
    def _seek_free(self, file):
        return self.findFreeEntry()

    # Converts a filename into a FAT short file name string.
    def _to_sfn(self, file):
        return file.split(".")[0][:8].ljust(8).upper() + file.split(".")[1][:3].ljust(3).upper()

    # Converts a filename into a FAT short file name byte array.
    def _to_sfn_b(self, file):
        return bytes(self._to_sfn(file), "ascii")

    # Returns the time in FAT format.
    def _get_time(self):
        return int((datetime.datetime.now().hour << 11) + (datetime.datetime.now().minute << 5) + (datetime.datetime.now().second // 2)).to_bytes(2, "little")

    # Returns the date in FAT format.
    def _get_date(self):
        return int(((datetime.datetime.now().year - 1980) << 9) + (datetime.datetime.now().month << 5) + datetime.datetime.now().day).to_bytes(2, "little")

    #######################
    # MAIN FUNCTIONS
    #######################

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

    def formatDisk(self, style):
        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Make sure the format style exists.
        if style not in self.disk_formats:
            raise SlitherIOError("FormatDoesNotExist", "The format doesn't exist!")

        self.attr = self.disk_formats[style]

        self.f.close()
        self.f = open(self.fp, "wb")

        # Number of logical sectors multiplied by bytes per sector.
        for i in range(self.attr["Logical_Sectors"] * self.attr["Bytes_Per_Sector"]):
            self.f.write(b'\x00')
        self.f.close()

        self.f = open(self.fp, "rb+")

        self.f.seek(0)
        self.f.write(b'\xEB\x3C\x90')

        #BPB
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

        # FAT ID
        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"])
        self.f.write(b"\xF0\xFF\xFF")


    ############################
    # CLUSTER CHAIN FUNCTIONS
    ############################

    # Returns a tuple of a cluster chain.
    def getChain(self, cluster):

        cc = [cluster]

        while cluster and (cluster < 0xFF0):

            # Calculate the location of the next cluster.
            fat_offset = int(cluster * 1.5)

            # Check if the current cluster is even or odd.
            even = cluster & 1

            # Load the next cluster.
            self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
            cluster = int.from_bytes(self.f.read(2), "little")

            # Adjust the 12-bit cluster appropriately.
            if even:
                cluster >>= 4
            else:
                cluster &= 0xFFF

            cc.append(cluster)

        return tuple(cc)

    # Loads the content of a cluster chain.
    def readChain(self, cluster):

        contents = bytes()

        # Get the cluster chain.
        cc = self.getChain(cluster)

        for i in cc:

            # Load the sector.
            self.f.seek(((i-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

            # Read cluster data.
            contents += self.f.read(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])

        return contents

    # Adds cluster(s) to the cluster chain.
    # TODO
    def growChain(self, clusters):
        pass

    # Removes cluster(s) from the cluster chain.
    # TODO
    def shrinkChain(self, clusters):
        pass

    # Completely removes the cluster chain.
    # TODO
    def deleteChain(self, clusters):
        pass

    # Creates a cluster chain.
    # TODO
    def makeChain(self, clusters):
        pass

    ############################
    # DIRECTORY FUNCTIONS
    ############################

    # Go to the directory path given.
    def goDir(self, sd):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        e = self.getDir()
        e_dir = [i for i in e if e[i]["IS_DIRECTORY"]]

        if sd in e_dir:
            self.dir_cluster = e[sd]["CLUSTER"]

            if sd == ".":
                pass
            elif sd == ".." and self.path != "./":
                self.path = self.path[:self.path[:-1].rfind("/")+1]
            else:
                self.path += "{}/".format(sd)

    # Finds a free entry and moves the file pointer there.
    def findFreeEntry(self):

        # We're at the root directory.
        if not self.dir_cluster:

            # Seek the start of the root directory.
            self._seek_root()

            # Start searching for the file.
            for i in range(self.attr["Dir_Entries"]):

                # Read the entry.
                fn = self.f.read(32)

                # Check to see if this is a free entry.
                if fn[0] in (0x00, 0xE5):
                        self.f.seek(-32, 1)
                        return True

        else:

            cluster = self.dir_cluster
            
            while cluster and (cluster < 0xFF0):

                # Load the sector.
                self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

                # Get a list of the file entry's LBA.
                for i in range(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"] // 32):
                    # Read the entry.
                    fn = self.f.read(32)

                    # Check to see if this is a free entry.
                    if fn[0] in (0x00, 0xE5):
                        self.f.seek(-32, 1)
                        return True

                # Read cluster data.
                contents += self.f.read(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])

                # Calculate the location of the next cluster.
                fat_offset = int(cluster * 1.5)

                # Check if the current cluster is even or odd.
                even = cluster & 1

                # Load the next cluster.
                self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                cluster = int.from_bytes(self.f.read(2), "little")

                # Adjust the 12-bit cluster appropriately.
                if even:
                    cluster >>= 4
                else:
                    cluster &= 0xFFF

        return False


    # Reads a directory and returns its content.
    def readDir(self):
        contents = bytes()

        sector_offsets = []
        
        # We're at the root directory.
        if not self.dir_cluster:

            # Seek the start of the root directory.
            self._seek_root()

            # Get a list of the file entry's LBA.
            for i in range(self.attr["Dir_Entries"]):
                sector_offsets.append(self.f.tell()+i*32)

            # Read the root directory.
            contents = self.f.read(32*self.attr["Dir_Entries"])

        else:

            cluster = self.dir_cluster
            
            while cluster and (cluster < 0xFF0):

                # Load the sector.
                self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

                # Get a list of the file entry's LBA.
                for i in range(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"] // 32):
                    sector_offsets.append(self.f.tell()+(i*32))

                # Read cluster data.
                contents += self.f.read(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])

                # Calculate the location of the next cluster.
                fat_offset = int(cluster * 1.5)

                # Check if the current cluster is even or odd.
                even = cluster & 1

                # Load the next cluster.
                self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                cluster = int.from_bytes(self.f.read(2), "little")

                # Adjust the 12-bit cluster appropriately.
                if even:
                    cluster >>= 4
                else:
                    cluster &= 0xFFF

        return contents, sector_offsets

    # Reads the Entry table for the current directory
    # and returns a dictonary of entries.
    def getDir(self, vFAT=False):

        entries = {}

        dir_data, sector_offsets = self.readDir()

        offset_count = 0

        l = []
        name = b""

        # Start searching through the root directory.
        while dir_data:

            # Read the entry.
            fn = dir_data[:32]
            dir_data = dir_data[32:]

            # If this entry is empty, we're done.
            if not fn[0]:
                break

            # If this entry is free, skip to the next.
            elif fn[0] == 0xE5:
                pass

            # FIX!
            # Check to see if this is a vFAT entry.
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
                l.append((name.decode(encoding="utf-16"),))
                name = b""

           # Otherwise this is a 8.3 entry.
            elif not (fn[11] & self.attr_flags["VOLUME_ID"] or fn[11] & self.attr_flags["LFN"]) :

                entry = {}

                # Read the entry.
                entry["SHORT_NAME"] = fn[:8].decode(encoding="ascii").rstrip()
                entry["SHORT_EXT"] = fn[8:11].decode(encoding="ascii").rstrip()
                entry["ATTRIBUTES"] = int(fn[11])
                entry["IS_READ_ONLY"] = bool(entry["ATTRIBUTES"] & self.attr_flags["READ_ONLY"])
                entry["IS_HIDDEN"] = bool(entry["ATTRIBUTES"] & self.attr_flags["HIDDEN"])
                entry["IS_SYSTEM"] = bool(entry["ATTRIBUTES"] & self.attr_flags["SYSTEM"])
                entry["IS_VOLUME_ID"] = bool(entry["ATTRIBUTES"] & self.attr_flags["VOLUME_ID"])
                entry["IS_DIRECTORY"] = bool(entry["ATTRIBUTES"] & self.attr_flags["DIRECTORY"])
                entry["IS_ARCHIVE"] = bool(entry["ATTRIBUTES"] & self.attr_flags["ARCHIVE"])
                entry["IS_FILE"] = not (entry["IS_VOLUME_ID"] or entry["IS_DIRECTORY"])
                entry["RESERVED"] = int(fn[12])
                entry["CREATION_TENTH_SECOND"] = int(fn[13])
                entry["CREATION_TIME"] = int.from_bytes(fn[14:16], "little")
                entry["CREATION_TIME_SECOND"] = (entry["CREATION_TIME"] & 0x1F) * 2
                entry["CREATION_TIME_MINUTE"] = (entry["CREATION_TIME"] >> 5) & 0x3F
                entry["CREATION_TIME_HOUR"] = (entry["CREATION_TIME"] >> 11) & 0x1F
                entry["CREATION_TIME_STR"] = "{:0>2}:{:0>2}:{:0>2}".format(entry["CREATION_TIME_HOUR"], entry["CREATION_TIME_MINUTE"], entry["CREATION_TIME_SECOND"])
                entry["CREATION_DATE"] = int.from_bytes(fn[16:18], "little")
                entry["CREATION_DATE_DAY"] = entry["CREATION_DATE"] & 0x1F
                entry["CREATION_DATE_MONTH"] = (entry["CREATION_DATE"] >> 5) & 0xF
                entry["CREATION_DATE_YEAR"] = ((entry["CREATION_DATE"] >> 9) & 0x7F) + 1980
                entry["CREATION_DATE_STR"] = "{:0>2}/{:0>2}/{}".format(entry["CREATION_DATE_MONTH"], entry["CREATION_DATE_DAY"], entry["CREATION_DATE_YEAR"]) #MMDDYYYY
                entry["ACCESSED_DATE"] = int.from_bytes(fn[18:20], "little")
                entry["ACCESSED_DATE_DAY"] = entry["ACCESSED_DATE"] & 0x1F
                entry["ACCESSED_DATE_MONTH"] = (entry["ACCESSED_DATE"] >> 5) & 0xF
                entry["ACCESSED_DATE_YEAR"] = ((entry["ACCESSED_DATE"] >> 9) & 0x7F) + 1980
                entry["ACCESSED_DATE_STR"] = "{:0>2}/{:0>2}/{}".format(entry["ACCESSED_DATE_MONTH"], entry["ACCESSED_DATE_DAY"], entry["ACCESSED_DATE_YEAR"]) #MMDDYYYY
                entry["HIGHER_CLUSTER"] = int.from_bytes(fn[20:22], "little")
                entry["MODIFIED_TIME"] = int.from_bytes(fn[22:24], "little")
                entry["MODIFIED_TIME_SECOND"] = (entry["MODIFIED_TIME"] & 0x1F) * 2
                entry["MODIFIED_TIME_MINUTE"] = (entry["MODIFIED_TIME"] >> 5) & 0x3F
                entry["MODIFIED_TIME_HOUR"] = (entry["MODIFIED_TIME"] >> 11) & 0x1F
                entry["MODIFIED_TIME_STR"] = "{:0>2}:{:0>2}:{:0>2}".format(entry["MODIFIED_TIME_HOUR"], entry["MODIFIED_TIME_MINUTE"], entry["MODIFIED_TIME_SECOND"])
                entry["MODIFIED_DATE"] = int.from_bytes(fn[24:26], "little")
                entry["MODIFIED_DATE_DAY"] = entry["MODIFIED_DATE"] & 0x1F
                entry["MODIFIED_DATE_MONTH"] = (entry["MODIFIED_DATE"] >> 5) & 0xF
                entry["MODIFIED_DATE_YEAR"] = ((entry["MODIFIED_DATE"] >> 9) & 0x7F) + 1980
                entry["MODIFIED_DATE_STR"] = "{:0>2}/{:0>2}/{}".format(entry["MODIFIED_DATE_MONTH"], entry["MODIFIED_DATE_DAY"], entry["MODIFIED_DATE_YEAR"]) #MMDDYYYY
                entry["LOWER_CLUSTER"] = int.from_bytes(fn[26:28], "little")
                entry["CLUSTER"] = (entry["HIGHER_CLUSTER"] << 16) + entry["LOWER_CLUSTER"]
                entry["SIZE"] = int.from_bytes(fn[28:32], "little")
                entry["SIZE_ON_DISK"] = self.getChain(len(self.getChain(entry["CLUSTER"]))*self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])

                # Generate a name for the file/directory.
                if entry["IS_DIRECTORY"] or not entry["SHORT_EXT"]:
                    entry["SHORT_FILE_NAME"] = entry["SHORT_NAME"]
                else:
                    entry["SHORT_FILE_NAME"] = "{}.{}".format(entry["SHORT_NAME"], entry["SHORT_EXT"])

                # Get the file entry's location in LBA.
                entry["LBA"] = sector_offsets[0]

                # Add the entry to the list of entries.
                entries[entry["SHORT_FILE_NAME"]] = entry

            del sector_offsets[0]

        return entries

    ############################
    # FILE FUNCTIONS
    ############################

    # Get the contents of a file off the disk.
    def readFile(self, file, vFAT=False):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Read the current directory.
        e = self.getDir()

        # Make sure the file exists.
        if file not in [i for i in e if e[i]["IS_FILE"]]:
            raise SlitherIOError("FileDoesNotExist", "The file doesn't exist!")

        # Return the file's content.
        return self.readChain(e[file]["CLUSTER"])[:e[file]["SIZE"]]

    # Creates a new, empty file.
    # TODO
    def newFile(self, file):
        pass

    # Appends a file.
    # TODO
    def appendFile(self, file):
        pass


    # Rename a file.
    def renameFile(self, oldname, newname):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # See if the new file exists already.
        if self._seek_file(newname):
            raise SlitherIOError("FileExists", "That file already exists!")

        # Seek the file entry.
        if not self._seek_file(oldname):
            raise SlitherIOError("FileDoesNotExist", "The file doesn't exist!")

        # Write the new file name.
        self.f.write(self._to_sfn_b(newname))

        print("Successfully renamed the file!")

        return True

    # Deletes a file if it exists.
    def deleteFile(self, file):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Seek the file entry.
        if not self._seek_file(file):
            raise SlitherIOError("FileDoesNotExist", "The file doesn't exist!")

        # Read the file entry.
        fn = self.f.read(32)

        # Save the start of the cluster chain. We need to clear that out too!
        cluster = int.from_bytes(fn[26:28], "little")

        # Mark the entry as deleted and clear it out.
        self.f.seek(-32, 1)
        self.f.write(b'\xE5' + b'\x00'*31)

        while cluster and (cluster < 0xFF0):

            # Calculate the location of the next cluster.
            fat_offset = int(cluster * 1.5)

            # Check if the current cluster is even or odd.
            even = cluster & 1

            # Load the next cluster.
            self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
            cluster = int.from_bytes(self.f.read(2), "little")
            self.f.seek(-2, 1)

            # Adjust the 12-bit cluster appropriately.
            if even:
                self.f.write((cluster & 0xF).to_bytes(2, "little"))
                cluster >>= 4
            else:
                self.f.write((cluster & 0xF000).to_bytes(2, "little"))
                cluster &= 0xFFF

        return True


    # Change to writeFile.
    def addFile(self, file, contents):
        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # If the file exists, delete it because we're overwriting it.
        if self._seek_file(file):
            self.deleteFile(file)

        # Seek the file entry.
        if not self._seek_free(file):
            raise SlitherIOError("NoFreeEntries", "There are no more free entries in the root directory!")

        file_size = len(contents)

        ent_loc = self.f.tell()

        # Write the file name.
        self.f.write(bytes(file.split(".")[0][:8].ljust(8).upper(), "ascii"))
        self.f.write(bytes(file.split(".")[1][:3].ljust(3).upper(), "ascii"))
        self.f.write(b'\x00') # Attributes.
        self.f.write(b'\x00') # Windows NT Flag
        self.f.write(b'\x00') # Creation time in tenths of a second.
        self.f.write(self._get_time()) #Creation time
        self.f.write(self._get_date()) # Creation date
        self.f.write(self._get_date()) # Last Access Date.
        self.f.write(b'\x00\x00') # Higher 16-bit cluster.
        self.f.write(self._get_time()) # Last modified time
        self.f.write(self._get_date()) # Last modified date.
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
            fat_offset = int(cluster * 1.5)

            # Check if the current cluster is odd.
            odd = cluster % 1

            # Get the next cluster.
            self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
            _cluster = int.from_bytes(self.f.read(2), "little")

            # Adjust the 12-bit cluster appropriately.
            if odd:
                _cluster >>= 4
            else:
                _cluster &= 0xFFF


            # If this cluster is free, add it to our list.
            if not _cluster:
                cluster_chain.append(cluster)
                sectors -= 1

            cluster += 1

        # Add an end of cluster.
        cluster_chain.append(0xFFF)
        last_cluster = 0

        for c in cluster_chain:


            # Only write if we have something left to write.
            if c != 0xFFF:

                # Load the cluster's sector(s).
                self.f.seek(((c-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

                # Write to the cluster's sector(s).
                self.f.write(contents[:self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]])
                contents = contents[self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]:]


            if last_cluster:

                # Calculate the location of the old cluster for the next cluster.
                fat_offset = int(last_cluster * 1.5)

                # Check if the last cluster is odd.
                odd = last_cluster & 1

                # Load the old cluster.
                self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+fat_offset)
                l = int.from_bytes(self.f.read(2), "little")

                # Add the current cluster in the old cluster's spot while preserving the 4 bit part of the neighboring cluster.
                if odd:
                    l = (c << 4) + (l & 0x000F)
                else:
                    l = c + (l & 0xF000)

                # Write the current cluster in the old cluster's spot.
                self.f.seek(-2, 1)
                self.f.write(l.to_bytes(2, "little"))

                last_cluster = c

            else:
                # Write the first cluster in the directory entry so we know where to start looking.
                self.f.seek(ent_loc+26)
                self.f.write(c.to_bytes(2, "little"))
                last_cluster = c

        return True

    def addBootloader(self, file, contents):
        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Fit the last data into the size of a sector, if needed.
        if len(contents) % self.attr["Bytes_Per_Sector"]:
            contents += b'\x00' * (self.attr["Bytes_Per_Sector"] - (len(contents) % self.attr["Bytes_Per_Sector"]))

        self.f.seek(0)

        self.f.write(contents)

if __name__ == "__main__":
    print("Not a standalone script!")
    exit(-1)
