import argparse

def process_m2_file(args):
    with open(args.m2_file, encoding='utf-8') as f:
        m2 = f.read().strip().split("\n\n")

    with open(args.out, "w", encoding='utf-8') as out:
        for sent in m2:
            sent = sent.split("\n")
            cor_sent = sent[0].split()[1:]
            out.write(" ".join(cor_sent)+"\n")


def main():
    parser = argparse.ArgumentParser(description='Process an .m2 file to extract the original text.')
    parser.add_argument("m2_file", help="The path to an input m2 file.")
    parser.add_argument("-out", help="A path to where we save the output corrected text file.", required=True)
    args = parser.parse_args()
    
    process_m2_file(args)

if __name__ == '__main__':
    main()