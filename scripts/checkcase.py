
import sys
import os
import os.path
import re
import xml.dom.minidom
import xml.dom
import argparse


def usage():
    print("""
usage:
    checkcase.py -f [fzp folder] -s [svg folder]
    ensure all fzp files case-sensitively match svg file names
    This will modify fzp files
""")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--fzp', dest='fzpdir',
                        help="fzp directory", default='.')
    parser.add_argument('-s', '--svg', dest='svgdir',
                        help="svg directort", default='svg')
    args = parser.parse_args()

    if not args.fzpdir:
        usage()
        parser.error("fzp dir argument not given")
        return -1

    if not args.svgdir:
        usage()
        parser.error("svg dir argument not given")
        return -1

    ret = 0
    svgdir = args.svgdir
    fzpdir = args.fzpdir
    allsvgs = []
    lowersvgs = {}
    for root, dirs, files in os.walk(svgdir, topdown=False):
        for filename in files:
            if not filename.endswith(".svg"):
                continue
            path = os.path.join(root, filename)
            allsvgs.append(path)
            lowersvgs[path.lower()] = path

    count_checks = 0
    count_fixes = 0
    count_missing = 0
    for root, dirs, files in os.walk(fzpdir, topdown=False):
        for filename in files:
            if not filename.endswith(".fzp"):
                continue

            count_checks += 1
            fzpFilename = os.path.join(root, filename)
            # if fzpFilename != "./core/SMD_SO14.fzp":
            #     continue

            try:
                dom = xml.dom.minidom.parse(fzpFilename)
            except xml.parsers.expat.ExpatError as err:
                print(str(err), fzpFilename)
                continue

            doUpdate = False
            fzp = dom.documentElement
            layerss = fzp.getElementsByTagName("layers")
            for layers in layerss:
                image = os.path.normpath(layers.getAttribute("image"))
                if ("dip_" in image) and ("mil_" in image):
                    continue
                if ("sip_" in image) and ("mil_" in image):
                    continue
                if ("jumper_" in image) and ("mil_" in image):
                    continue
                if ("screw_terminal_" in image):
                    continue
                if ("jumper" in image):
                    continue
                if ("mystery_" in image):
                    continue
                if ("LED-" in image):
                    continue
                if ("axial_lay" in image):
                    continue
                if ("resistor_" in image):
                    continue
                if ("generic" in image) and ("header" in image):
                    continue

                for subpath in ['core', 'contrib', 'obsolete']:
                    path = os.path.join(svgdir, subpath, image)
                    if not lowersvgs.get(path.lower()) is None:
                        if not path in allsvgs:
                            print("mismatch", fzpFilename)
                            print("\t", path)
                            print("\t", lowersvgs.get(path.lower()))
                            print()
                            thing = layers.getAttribute("image").split("/")
                            thing[1] = os.path.basename(lowersvgs[path.lower()])
                            layers.setAttribute("image", "/".join(thing))
                            doUpdate = True
                        break
                else: # yes, for ... else
                    # TODO: Fix missing files in fritzing-parts repo, so we can treat this as error
                    print("Warning: missing", fzpFilename, image)
                    count_missing += 1

            if doUpdate:
                count_fixes += 1
                if sys.version_info >= (3,8,0):
                    outfile = open(fzpFilename, 'wb')
                    s = dom.toxml("UTF-8")
                    outfile.write(s)
                    outfile.close()
                ret = -1

    print("%s fzp files checked." % count_checks)
    print("%s fzp case-sensitivity errors found." % count_fixes)
    if count_fixes > 0 and sys.version_info < (3,8,0):
        print("Fixes not applied. Please use at least python 3.8 to preserve attributes order. This is important for human readability of xml files.")

    print("%s svg file references broken." % count_missing )
    return ret


if __name__ == "__main__":
    sys.exit(main())
