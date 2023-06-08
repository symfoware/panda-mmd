import argparse 
import mmd.converter as converter

# python3 convert.py dist/miku/Lat式ミクVer2.31_Normal.pmd dist/test.egg
# python3 convert.py dist/alicia/Alicia_solid.pmx dist/test.egg

def main(mmd_file, egg_file):
    egg = converter.convert(mmd_file)
    if not egg:
        return

    with open(egg_file, 'w') as f:
        f.write(egg)

    print('convert end %s to %s.' % (mmd_file, egg_file))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='pmd/pmx to egg converter',
        description='pmd/pmx形式のファイルをPanda3D egg形式に変換'
    )
    parser.add_argument(
        'mmd_file',
        metavar='input pmd/pmx file',
        type=str,
        help='変換するpmd/pmxのファイルパスを指定'
    )
    parser.add_argument(
        'egg_file',
        metavar='output egg file',
        type=str,
        help='変換後のeggファイルの出力先パスを指定'
    )
    args = parser.parse_args()
    main(args.mmd_file, args.egg_file)