from parser import FilmsParser

if __name__ == '__main__':
    PARSER = FilmsParser(parse_format='json', pages_count=1)
    PARSER.parse()
