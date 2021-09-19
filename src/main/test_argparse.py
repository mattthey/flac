import argparse


def main():
    parser = argparse.ArgumentParser(description='process some integers')
    parser.add_argument('integers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulat', action='store_const',
                        const=sum, default=max, required=False,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print(args.accumulat(args.integers))


if __name__ == '__main__':
    main()
