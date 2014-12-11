import sys, os, struct, json, binascii

running_offset = 0
pak01_000 = None

def add_file(ext_path_file, ext, path, file):
    if path.startswith("./"):
        path = path[2:]
    if ext in ext_path_file:
        xpath = ext_path_file[ext]
    else:
        ext_path_file[ext] = { }
        xpath = ext_path_file[ext]
    if path in xpath:
        xpath[path].append(file)
    else:
        xpath[path] = [file]

def write_file_entry(pak01_dir, srcfile):
    global running_offset
    global pak000
    if srcfile[:2] == " /":
        srcfile = "." + srcfile[1:]
    with open(srcfile, "rb") as src:
        data = src.read()
        pak01_dir.write(struct.pack('I', binascii.crc32(data) & 0xffffffff)) # CRC32
        pak01_dir.write(struct.pack('H', 0)) # Preload bytes
        pak01_dir.write(struct.pack('H', 0)) # Archive file index
        pak01_dir.write(struct.pack('I', running_offset)) # Offset into archive
        pak01_dir.write(struct.pack('I', len(data))) # File length
        pak01_dir.write(struct.pack('H', 0xffff))
        running_offset += len(data)
        pak01_000.write(data) # Add the file contents to the main pak

def make_vpk(srcdir, dstdir):
    global running_offset
    global pak01_000
    old_wd = os.getcwd()
    running_offset = 0
    dstdir = os.path.abspath(dstdir)
    os.chdir(srcdir)
    srcdir = "."
    with open(os.path.join(dstdir, "pak01_dir.vpk"), "wb") as pak01_dir:
        # Write VPK header
        pak01_dir.write(struct.pack('I', 0x55aa1234)) # Magic signature
        pak01_dir.write(struct.pack('I', 1)) # Version
        pak01_dir.write(struct.pack('I', 0)) # Directory length -- filled later
        # Prepare dictionary for VPK directory
        ext_path_file = {}
        for root, dirs, files in os.walk(srcdir):
            for f in files:
                path = os.path.join(root, f)
                ext = os.path.splitext(path)[1]
                if ext == "":
                    ext = " "
                if ext[0] == ".":
                    ext = ext[1:]
                if root == "" or root == ".":
                    root = " "
                add_file(ext_path_file, ext, root, f)
        print "Collected files for VPK:", len(ext_path_file), "unique extensions."
        #print "VPK Structure:"
        #print json.dumps(ext_path_file, indent=4)
        # Write VPK directory and pak000
        pak01_000 = open(os.path.join(dstdir, "pak01_000.vpk"), "wb")
        for ext, path_map in ext_path_file.iteritems():
            pak01_dir.write(ext)
            pak01_dir.write(struct.pack('B', 0))
            for path, filenames in path_map.iteritems():
                pak01_dir.write(path)
                pak01_dir.write(struct.pack('B', 0))
                for filename in filenames:
                    if ext == " ":
                        filename_noext = filename
                    else:
                        filename_noext = filename[:-(len(ext) + 1)]
                    pak01_dir.write(filename_noext)
                    pak01_dir.write(struct.pack('B', 0))
                    real_path = os.path.join(path, filename)
                    write_file_entry(pak01_dir, real_path)
                pak01_dir.write(struct.pack('B', 0))
            pak01_dir.write(struct.pack('B', 0))
        pak01_dir.write(struct.pack('B', 0))
        pak01_000.close()
        # Fix VPK header directory length
        size = pak01_dir.tell()
        pak01_dir.seek(8)
        pak01_dir.write(struct.pack('I', size - 3 * 4))
    os.chdir(old_wd)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: python vpk.py source-dir out-dir"
        exit(1)
    srcdir = sys.argv[1]
    dstdir = sys.argv[2]
    make_vpk(srcdir, dstdir)
