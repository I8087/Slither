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
            self.f.seek(e[file]["SFN_LBA"])
            return True
        else:
            return False

    # Seeks a free entry.
    # Deprecated. Use findFreeEntry()
    def _seek_free(self, file, n=1):
        return self.findFreeEntry(n)

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
    # ENTRY NAME FUNCTIONS
    ############################

    # Takes a file name and returns the appropriate type.
    def toFN(self, name):
        if self.isSFN(name):
            return self.toSFN(name)
        else:
            return self.toLFN(name)

    # Takes a file name and returns the appropriate type in bytes.
    def toFNb(self, name):
        if self.isSFN(name):
            return self.toSFNb(name)
        else:
            return self.toLFNb(name)

    # Checks to see if this is a valid short name.
    def isSFN(self, name):

        # Make sure there's an actual name.
        if len(name) == 0:
            return False

        # Split the file name into a name and extension.
        dot = name.rfind(".")

        if dot != -1:
            s_name = name[:dot]
            s_ext = name[dot+1:]
        else:
            s_name = name
            s_ext = ""

        # Make sure the name and extension are within size limits.
        if len(s_name) > 8 or len(s_ext) > 3:
            return False

        # Make sure the name and extension have legal characters.
        for i in s_name+s_ext:
            if not self.legalSFNchar(i):
                return False

        return True

    # Checks to see if this is a valid long name.
    # TODO
    def isLFN(self, name):
        pass


    # Turns file name into a SFN entry.
    def toSFN(self, name):
        if self.isSFN(name):
            return name.split(".")[0][:8].ljust(8) + name.split(".")[1][:3].ljust(3)
        else:
            return False

    # Return a SFN in bytes.
    def toSFNb(self, name):
        r = self.toSFN(name)
        if r:
            # Split the file name into a name and extension.
            if "." in name:
                s_name, s_ext = name.split(".")
            else:
                s_name = name
                s_ext = ""
            return bytes(s_name.ljust(8)+s_ext.ljust(3), "cp437")

        return False

    # Turns file name into a tuple of each LFN entry.
    def toLFN(self, name):
        return tuple([name[i:i+13] for i in range(0, len(name), 13)][::-1])

    # Return a SFN in bytes.
    def toLFNb(self, name):
        r = self.toLFN(name+"\uFFFF")
        if r:
            return tuple([bytes(r[i].ljust(13, "\u0000") , "utf-16-le") for i in range(len(r))])
        else:
            return False

        return r

    # Creates a new duplicated SFN.
    def dupSFN(self, name):

        # Make sure this is a valid SFN.
        if not self.isSFN(name):
            return False

        # Get a list of SFN in the directory.
        e = self.getDir()
        e_names = tuple([e[i]["SHORT_FILE_NAME"] for i in e])

        # Make sure this file does exist, otherwise just give back the orignal SFN!
        if name not in e_names:
            return name

        # Split the file name into a name and extension.
        if "." in name:
            s_name, s_ext = name.split(".")
        else:
            s_name = name
            s_ext = ""

        for i in range(1000):
            new_name = "{}~{}.{}".format(s_name[:7-len(str(i))], i, s_ext)
            if new_name not in e_names:
                return new_name


    # Makes a SFN from a LFN.
    def makeSFN(self, name):

        # Lowercase letters aren't allowed in SFN.
        name = name.upper()

        # See if there's a file extension.
        dot = name.rfind(".")

        if dot != -1:
            s_name = name[:dot]
            s_ext = name[dot+1:]
            dot = "."
        else:
            s_name = name
            s_ext = ""
            dot = ""

        # New SFN holder.
        new_name = ""
        new_ext = ""

        # Convert illegal characters in the file name.
        for i in s_name:
            if self.legalSFNchar(i):
                new_name = new_name + i
            else:
                new_name = new_name + "~"

        # Convert illegal characters in the file extension.
        for i in s_ext:
            if self.legalSFNchar(i):
                new_ext = new_ext + i
            else:
                new_ext = new_ext + "~"

        # Split file name holders.
        f_name = ""
        l_name = ""

        if len(new_name) <= 8:
            f_name = new_name
        else:
            f_name = new_name[:4]
            l_name = new_name[-4:]

        return "{}{}{}{}".format(f_name, l_name, dot, new_ext[:3])


    # Creates a fake SFN for a LFN.
    def fakeSFN(self, name):
        return self.dupSFN(self.makeSFN(name))

    # Returns True if the character is allowed in a SFN, otherwise it returns false.
    def legalSFNchar(self, char):
        if ord(char) in (0x20, 0x21, 0x2D, 0x40, 0x7B, 0x7D, 0x7E) or 0x23 <= ord(char) <= 0x29 or 0x30 <= ord(char) <= 0x39 or 0x41 <= ord(char) <= 0x5A or 0x5E <= ord(char) <= 0x60 or 0x80 <= ord(char) <= 0xFF:
            return True
        else:
            return False

    # Generate a checksum for a LFN from a SFN.
    def gensumLFN(self, name):

        # Create a new checksum to verify with the current checksum.
        ns = 0

        for i in name:
            ns = (((ns & 1) << 7) + (ns >> 1) + ord(i)) & 0xFF

        return ns

    # Make sure the checksum for the LFN match the SFN.
    def checksumLFN(self, name, cs):
        return self.gensumLFN(name) == cs

    # Splits a LFN into SFN entries.
    def splitLFN(self, name):

        # List of LFN parts.
        LFNS = []

        # Add a null character.
        name += "\u0000"

        while name:
            LFNS.append(name[:13].ljust(13, "\uFFFF"))
            name = name[13:]

        return tuple(LFNS[::-1])

    ############################
    # ENTRY EXISTS FUNCTIONS
    ############################

    # Checks to see if that entry exists.
    def doesExist(self, entry):

        # Get a list of everything in the current directory.
        e = self.getDir()

        if entry in e.keys():
            return True

        return False

    # Checks to see if a file exists.
    def fileExists(self, file):

        # Get a list of files in the directory.
        e = self.getDir()
        if file in [i for i in e if e[i]["IS_FILE"]]:
            return True

        return False

    # Checks to see if a directory exists.
    def dirExists(self, directory):

        # Get a list of files in the directory.
        e = self.getDir()
        if directory in [i for i in e if e[i]["IS_DIRECTORY"]]:
            return True

        return False

    ############################
    # TIME & DATE FUNCTIONS
    ############################

    # Returns the time in FAT format.
    def getTime(self):
        return int((datetime.datetime.now().hour << 11) + (datetime.datetime.now().minute << 5) + (datetime.datetime.now().second // 2)).to_bytes(2, "little")

    # Returns the date in FAT format.
    def getDate(self):
        return int(((datetime.datetime.now().year - 1980) << 9) + (datetime.datetime.now().month << 5) + datetime.datetime.now().day).to_bytes(2, "little")


    ############################
    # CLUSTER CHAIN FUNCTIONS
    ############################

    # Returns a tuple of a cluster chain.
    def getChain(self, cluster):

        cc = [cluster]

        while cluster and (cluster < 0xFF0):

            cluster = self.nextChain(cluster)
            cc.append(cluster)

        return tuple(cc)

    # Loads the content of a cluster chain.
    def readChain(self, cluster):

        contents = bytes()

        for i in self.getChain(cluster):

            # Read cluster data.
            contents += self.readCluster(i)

        return contents

    # Adds cluster(s) to the cluster chain.
    # TODO
    def growChain(self, cluster, clusters):
        pass

    # Removes cluster(s) from the cluster chain.
    # TODO
    def shrinkChain(self, cluster, clusters):
        pass

    # Grows or shrinks the cluster chain based on number of clusters needed.
    def setChain(self, cluster, clusters):
        pass

    # Completely removes the cluster chain.
    def deleteChain(self, cluster):

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

    # Creates a cluster chain.
    def makeChain(self, clusters):

        cluster = 0
        cluster_chain = []

        while clusters:

            # Get the next cluster.
            self.seekChain(cluster)
            _cluster = int.from_bytes(self.f.read(2), "little")

            # Adjust the 12-bit cluster appropriately.
            if cluster & 1:
                _cluster >>= 4
            else:
                _cluster &= 0xFFF


            # If this cluster is free, add it to our list.
            if not _cluster:
                cluster_chain.append(cluster)
                clusters -= 1

            cluster += 1

        last_cluster = 0

        for cluster in cluster_chain+[0xFFF]:

            if last_cluster:
                # Load the last cluster.
                self.seekChain(last_cluster)
                c = int.from_bytes(self.f.read(2), "little")

                # Add the current cluster in the old cluster's spot while preserving the 4 bit part of the neighboring cluster.
                if last_cluster & 1:
                    c = (cluster << 4) + (c & 0x000F)
                else:
                    c = cluster + (c & 0xF000)

                # Write the current cluster in the old cluster's spot.
                self.f.seek(-2, 1)
                self.f.write(c.to_bytes(2, "little"))

            last_cluster = cluster

        return cluster_chain


    # Finds the next cluster in the chain.
    def nextChain(self, cluster):

        # Load the next cluster.
        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+int(cluster*1.5))
        next_cluster = int.from_bytes(self.f.read(2), "little")

        # Adjust the 12-bit cluster appropriately.
        if cluster & 1:
            next_cluster >>= 4
        else:
            next_cluster &= 0xFFF

        return next_cluster

    # Seeks the location of the cluster.
    def seekChain(self, cluster):
        self.f.seek(self.attr["Reserved_Sectors"]*self.attr["Bytes_Per_Sector"]+int(cluster*1.5))

    # Reads the sector(s) in that cluster.
    def readCluster(self, cluster):
        # Load the sector.
        self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

        # Read the cluster data.
        return self.f.read(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"])

    # Writes to the sector(s) in that cluster.
    def writeCluster(self, cluster, content):
        # Load the sector(s) in the cluster.
        self.f.seek(((cluster-2) * self.attr["Sectors_Per_Cluster"] + self.getFirstDataSector()) * self.attr["Bytes_Per_Sector"])

        # Write the cluster data.
        self.f.write(content[:self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]])

    # Wipes the sector(s) in that cluster blank.
    def wipeCluster(self, cluster):
        self.writeCluster(cluster, b"\x00"*(self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]))

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

    # Edits the values of an entry.
    def editEntry(self, name, entry, new_entry):

        # Remove the old entry.
        self.removeEntry(entry)

        # Update the entry with the new data.
        entry.update(new_entry)

        # Create a new entry.
        self.newEntry(entry["FILE_NAME"], entry)

        return True

    # Creates a new entry.
    def newEntry(self, name, entry):

        # A tuple of LFN parts.
        LFNS = ()

        e = self.getDir()

        # Make sure this entry exists.
        if name in e.keys():
            raise SlitherIOError("EntryExists", "This entry already exists!")

        # Check to see if this is a LFN.
        if not self.isSFN(name):
            LFNS = self.splitLFN(name)
            name = self.fakeSFN(name)

        # Split the SFN.
        if "." in name:
            file_name, file_ext = name.split(".")
        else:
            file_name = name
            file_ext = ""

        # Generate a checksum.
        cs = self.gensumLFN(file_name.ljust(8)+file_ext.ljust(3))


        # Find enough free entries.
        entries = self.findFreeEntry(len(LFNS)+1)

        # Not enough free entries!
        if not entries:
            return False

        self.f.seek(entries[0])

        # Write each LFN entry.
        for i in range(len(LFNS)):

            # Is this the last LFN entry?
            if len(LFNS)-i == len(LFNS):
                self.f.write((len(LFNS)+0x40).to_bytes(1, "little"))
            else:
                self.f.write(len(LFNS).to_bytes(1, "little"))

            self.f.write(bytes(LFNS[i][:5], "utf-16-le"))
            self.f.write(self.attr_flags["LFN"].to_bytes(1, "little"))
            self.f.write(bytes(1))
            self.f.write(cs.to_bytes(1, "little"))
            self.f.write(bytes(LFNS[i][5:11], "utf-16-le"))
            self.f.write(bytes(2))
            self.f.write(bytes(LFNS[i][11:13], "utf-16-le"))

        # Update the SFN entry.
        self.f.write(bytes(file_name.ljust(8), "ascii"))
        self.f.write(bytes(file_ext.ljust(3), "ascii"))
        self.f.write(entry["ATTRIBUTES"].to_bytes(1, "little"))
        self.f.write(entry["RESERVED"].to_bytes(1, "little"))
        self.f.write(entry["CREATION_TENTH_SECOND"].to_bytes(1, "little"))
        self.f.write(entry["CREATION_TIME"].to_bytes(2, "little"))
        self.f.write(entry["CREATION_DATE"].to_bytes(2, "little"))
        self.f.write(entry["ACCESSED_DATE"].to_bytes(2, "little"))
        self.f.write(entry["HIGHER_CLUSTER"].to_bytes(2, "little"))
        self.f.write(entry["MODIFIED_TIME"].to_bytes(2, "little"))
        self.f.write(entry["MODIFIED_DATE"].to_bytes(2, "little"))
        self.f.write(entry["LOWER_CLUSTER"].to_bytes(2, "little"))
        self.f.write(entry["SIZE"].to_bytes(4, "little"))

        return True

    # Frees up an entry.
    def removeEntry(self, entry):

        entries = entry["LFN_LBA"]
        entries.append(entry["SFN_LBA"])

        # Remove each entry associated with the file.
        for i in entries:
            self.f.seek(i)
            self.f.write(b'\xE5' + bytes(31))

        return True

    # Finds free entries and returns a list of LBAs.
    def findFreeEntry(self, n=1):

        # A chain of entries. Needed for LFNs.
        entries = []

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
                    entries.append(self.f.tell()-32)

                    # Return if we have enough entries.
                    if len(entries) == n:
                        return tuple(entries)
                else:
                    entries = []

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
                        entries.append(self.f.tell()-32)
                        # Return if we have enough entries.
                        if len(entries) == n:
                            return tuple(entries)
                    else:
                        entries = []

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

        # Return the chain of entries.
        return tuple()


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
    def getDir(self, vFAT=True):

        entries = {}

        dir_data, sector_offsets = self.readDir()

        offset_count = 0

        # LFN holder
        LFN = []

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
            elif vFAT and fn[11] == self.attr_flags["LFN"]:
                name_part = fn[1:11] + fn[14:26] + fn[28:32]
                name_part = name_part.decode("utf-16-le")

                # If this is the end of the LFN, cut off the excess.
                if "\u0000" in name_part:
                    name_part = name_part.split("\u0000")[0]

                LFN.append((int(fn[0]), int(fn[13]), name_part, sector_offsets[0]))

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

                # Check for a LFN.
                entry["LONG_FILE_NAME"] = ""

                # Make sure the checksum matches.
                LFN = [i for i in LFN if self.checksumLFN(entry["SHORT_NAME"].ljust(8)+entry["SHORT_EXT"].ljust(3), i[1])]

                for i in LFN[::-1]:
                    entry["LONG_FILE_NAME"] += i[2]

                # Generate a name for the file/directory.
                if entry["IS_DIRECTORY"] or not entry["SHORT_EXT"]:
                    entry["SHORT_FILE_NAME"] = entry["SHORT_NAME"]
                else:
                    entry["SHORT_FILE_NAME"] = "{}.{}".format(entry["SHORT_NAME"], entry["SHORT_EXT"])

                # Get the file entry's location in LBA.
                entry["SFN_LBA"] = sector_offsets[0]
                entry["LFN_LBA"] = [i[3] for i in LFN]

                # Set the file entry name.
                if entry["LONG_FILE_NAME"]:
                    entry["FILE_NAME"] = entry["LONG_FILE_NAME"]
                else:
                    entry["FILE_NAME"] = entry["SHORT_FILE_NAME"]

                # Add the entry to the list of entries.
                entries[entry["FILE_NAME"]] = entry

                # Clean up the LFN for the next entry.
                LFN = []

            del sector_offsets[0]

        return entries

    ############################
    # FILE FUNCTIONS
    ############################

    # Creates a new, empty file.
    # TODO
    def newFile(self, file):
        pass

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

    def writeFile(self, file, contents):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # If the file exists, delete it because we're overwriting it.
        if self.fileExists(file):
            self.deleteFile(file)

        elif self.doesExist(file):
            raise SlitherIOError("NotFile", "Can't write to a nonfile!")

        file_size = len(contents)

        # Find the number of clusters needed.
        sectors = file_size // self.attr["Bytes_Per_Sector"]

        # Fit the last data into the size of a sector, if needed.
        if file_size % self.attr["Bytes_Per_Sector"]:
            contents += b'\x00' * (self.attr["Bytes_Per_Sector"] - (file_size % self.attr["Bytes_Per_Sector"]))
            sectors += 1

        # Make a cluster chain.
        cluster_chain = self.makeChain(sectors)

        # Write the data to the disk.
        for cluster in cluster_chain:
            self.writeCluster(cluster, contents[:self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]])
            contents = contents[self.attr["Sectors_Per_Cluster"] * self.attr["Bytes_Per_Sector"]:]

        # Update the entry.
        entry = {}
        entry["FILE_NAME"] = file
        entry["ATTRIBUTES"] = 0
        entry["RESERVED"] = 0
        entry["CREATION_TENTH_SECOND"] = 0
        entry["CREATION_TIME"] = int.from_bytes(self.getTime(), "little")
        entry["CREATION_DATE"] = int.from_bytes(self.getDate(), "little")
        entry["ACCESSED_DATE"] = int.from_bytes(self.getDate(), "little")
        entry["HIGHER_CLUSTER"] = 0
        entry["MODIFIED_TIME"] = int.from_bytes(self.getTime(), "little")
        entry["MODIFIED_DATE"] = int.from_bytes(self.getDate(), "little")
        entry["LOWER_CLUSTER"] = cluster_chain[0]
        entry["SIZE"] = file_size

        # Create the new entry within the directory.
        self.newEntry(file, entry)

        return True

    # Appends a file.
    # TODO
    def appendFile(self, file):
        pass


    # Rename a file.
    def renameFile(self, old_name, new_name):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Read the current directory.
        e = self.getDir()

        # Make sure the file exists.
        if not self.fileExists(old_name):
            raise SlitherIOError("FileDoesNotExist", "The file doesn't exist!")

        # Make sure the new file name isn't already taken!
        if self.fileExists(new_name):
            raise SlitherIOError("FileExists", "The new file name already exists!")

        

        # Edit the directory entry.
        self.editEntry(old_name, e[old_name], {"FILE_NAME": new_name})

        return True

    # Deletes a file if it exists.
    def deleteFile(self, file):

        # Make sure the disk is mounted first!
        if not self.isMounted():
            raise SlitherIOError("NotMounted", "No disk mounted!")

        # Read the current directory.
        e = self.getDir()

        # Make sure the file exists.
        if file not in [i for i in e if e[i]["IS_FILE"]]:
            raise SlitherIOError("FileDoesNotExist", "The file doesn't exist!")

        # Remove the file entries associated with the file.
        self.removeEntry(e[file])

        # Remove the cluster chain associated with the file.
        self.deleteChain(e[file]["CLUSTER"])

        return True

    # Change to writeFile.
    def addFile(self, file, contents):
        self.writeFile(file, contents)

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
    a = FAT12()
    a.mount("../mikeos.flp")
    for i in a.getDir().keys():
        print(i)
    a.unmount()
    print("Not a standalone script!")
    exit(-1)
