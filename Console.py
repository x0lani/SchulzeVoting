import Schulze
import os
import random


def poll_file(poll_name: str) -> str:
    """
Take a poll ID string and convert it to the matching filename containing metadata
    :param poll_name: test
    :return: poll file name like  'XXXXXXX.choices.txt'
    """
    return poll_name + '.choices.txt'


def poll_ID(poll_filename: str) -> str:
    """
Given a filename containing poll metadata, return the poll ID
    :param poll_filename: poll file name like  'choices.XXXXXXX.txt'
    :return: poll ID
    """
    poll_name = poll_filename.split('.')[:-2]  # remove 'choices.' and '.txt'
    poll_name = '.'.join(poll_name)
    return poll_name


def new_poll(output_dir='.'):
    name = input('What is the name of your new poll?\n')
    num = int(input('How many choices will there be? '))
    option = []
    for i in range(num):
        print('Option #{}> '.format(i), end='')
        entry = input()
        if entry not in option:  # prevent duplicates
            option.append(entry)
    output_file = os.path.join(output_dir, poll_file(name))
    with open(output_file, mode='w') as fout:
        for o in option:
            fout.write(o)
            fout.write('\n')
    return option


def load_poll(poll_name, voting_dir='.'):
    in_file = os.path.join(voting_dir, poll_file(poll_name))
    options = []
    with open(in_file, mode='r') as fin:
        for line in fin:
            options.append(line.strip())
    return options


def admin_console(voting_dir='.\\votes'):
    # Initialize directory structure if needed
    if not os.path.exists(voting_dir):
        os.mkdir(voting_dir)
    voting_dir = os.path.abspath(voting_dir)

    polls = get_polls(voting_dir)
    if len(polls):
        print('{} polls found in {}...'.format(len(polls), voting_dir))
        for i, p in enumerate(polls):
            print('{})\t{}'.format(i, p))
    else:
        print('No polls found in {}...'.format(voting_dir))
    print('N)\tCreate new poll')
    if len(polls) > 0:
        choices = [str(c) for c in list(range(len(polls)))]
    else:
        choices = []
    choices += 'N'
    choice = ''
    while choice not in choices:
        choice = input('> ')[0].upper()
    if choice == 'N':
        candidates = new_poll(voting_dir)
    else:
        candidates = load_poll(polls[int(choice)], voting_dir)
    print('Candidates are:')
    print(candidates)
    return


def get_polls(vote_dir):
    # Find all current elections
    polls = []
    for entry in os.scandir(vote_dir):
        # find choices.*.txt
        if entry.is_file() and entry.name.endswith('.choices.txt'):
            polls.append(poll_ID(entry.name))
    return polls


def voting_console(poll_name, vote_dir='.\\votes'):
    valid = False
    choices = load_poll(poll_name, vote_dir)
    ID = hex(random.randrange(65536))[2:]  # generate a random ID number for this ballot
    ID = ID.upper()
    rank = []
    print('Ballot #{}'.format(ID))
    while not valid:
        print('The choices are:')
        for i, c in enumerate(choices):
            print('\t{}>\t{}'.format(i + 1, c))
        for i in range(len(choices)):
            print('Select choice #{} :'.format(i + 1), sep='')
            selection = int(input()[0])
            rank.append(choices[selection - 1])
        print('\nYour ballot:')
        print('************')
        print('Ballot #{}'.format(ID))
        for i, c in enumerate(rank):
            print('\t{}) {}'.format(i, c))
        print('\nIs this correct? (Y/N) ', sep='')
        if input().lower() == 'y':
            valid = True
        else:
            rank.clear()
    file_name = '.'.join([poll_name, ID, 'ballot.txt'])
    with open(os.path.join(vote_dir, file_name), mode='w') as fout:
        for choice in rank:
            fout.write(choice)
            fout.write('\n')
    return rank


def tally_votes(poll_name, vote_dir='.\\votes'):
    vote_files = []
    for entry in os.scandir(vote_dir):
        # find .ballot.txt
        if entry.is_file() and entry.name.startswith(poll_name) and entry.name.endswith('.ballot.txt'):
            vote_files.append(os.path.join(vote_dir, entry.name))
    ballots = [read_ballot(b) for b in vote_files]
    total = ballots[0]  # initialize total
    for b in ballots[1:]:
        total += b
    return total


def read_ballot(ballot_file):
    ID = ballot_file.split('.')[-3]
    vote = []
    with open(ballot_file, mode='r') as fin:
        for line in fin:
            vote.append(line.strip())
    return Schulze.Ballot(vote, ID)


def main():
    pass


if __name__ == '__main__':
    main()
