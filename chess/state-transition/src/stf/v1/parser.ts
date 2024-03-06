import type { ParserRecord } from '@paima/sdk/concise';
import { PaimaParser } from '@paima/sdk/concise';
import type {
  BotMove,
  ClosedLobbyInput,
  CreatedLobbyInput,
  JoinedLobbyInput,
  ParsedSubmittedInput,
  SubmittedMovesInput,
  UserStats,
  ZombieRound,
  CardanoTransfer,
  CardanoStakeDelegation,
  CardanoProjectedNft,
  CardanoMint,
} from './types';
import { ENV } from '@paima/sdk/utils';

const myGrammar = `
createdLobby        = c|numOfRounds|roundLength|playTimePerPlayer|isHidden?|isPractice?|botDifficulty|playerOneIsWhite?
joinedLobby         = j|*lobbyID
closedLobby         = cs|*lobbyID
submittedMoves      = s|*lobbyID|roundNumber|pgnMove
zombieScheduledData = z|*lobbyID
userScheduledData   = u|*user|result|ratingChange
scheduledBotMove   = sb|*lobbyID|roundNumber
cardanoTransfer  = ct|txId|metadata|inputCredentials|outputs
cardanoDelegation  = cd|address|pool
projectedNft = pnft|ownerAddress|previousTxHash|previousOutputIndex|currentTxHash|currentOutputIndex|policyId|assetName|status
cardanoMint = cmb|txId|metadata|assets
`;

const createdLobby: ParserRecord<CreatedLobbyInput> = {
  numOfRounds: PaimaParser.NumberParser(3, 1000),
  roundLength: PaimaParser.DefaultRoundLength(ENV.BLOCK_TIME),
  playTimePerPlayer: PaimaParser.NumberParser(1, 100000),
  isHidden: PaimaParser.TrueFalseParser(false),
  isPractice: PaimaParser.TrueFalseParser(false),
  botDifficulty: PaimaParser.NumberParser(0, 3),
  playerOneIsWhite: PaimaParser.TrueFalseParser(true),
};
const joinedLobby: ParserRecord<JoinedLobbyInput> = {
  lobbyID: PaimaParser.NCharsParser(12, 12),
};
const closedLobby: ParserRecord<ClosedLobbyInput> = {
  lobbyID: PaimaParser.NCharsParser(12, 12),
};
const submittedMoves: ParserRecord<SubmittedMovesInput> = {
  lobbyID: PaimaParser.NCharsParser(12, 12),
  roundNumber: PaimaParser.NumberParser(1, 10000),
  // PGN http://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm
  // move validity checked by external library, out of scope for this parser.
  pgnMove: PaimaParser.NCharsParser(2, 255),
};
const zombieScheduledData: ParserRecord<ZombieRound> = {
  renameCommand: 'scheduledData',
  effect: 'zombie',
  lobbyID: PaimaParser.NCharsParser(12, 12),
};
const userScheduledData: ParserRecord<UserStats> = {
  renameCommand: 'scheduledData',
  effect: 'stats',
  user: PaimaParser.WalletAddress(),
  result: PaimaParser.RegexParser(/^[w|t|l]$/),
  ratingChange: PaimaParser.NumberParser(),
};
const scheduledBotMove: ParserRecord<BotMove> = {
  renameCommand: 'scheduledData',
  effect: 'move',
  lobbyID: PaimaParser.NCharsParser(12, 12),
  roundNumber: PaimaParser.NumberParser(1, 10000),
};
const cardanoTransfer: ParserRecord<CardanoTransfer> = {
  txId: PaimaParser.NCharsParser(0, 64),
  metadata: PaimaParser.OptionalParser(null, PaimaParser.RegexParser(/[a-f0-9]*/)),
  inputCredentials: PaimaParser.ArrayParser({
    item: PaimaParser.RegexParser(/[a-f0-9]*/),
  }),
  outputs: (keyName: string, input: string) => {
    return JSON.parse(input);
  },
};
const cardanoDelegation: ParserRecord<CardanoStakeDelegation> = {
  address: PaimaParser.NCharsParser(0, 100),
  pool: PaimaParser.OptionalParser(null, PaimaParser.NCharsParser(0, 100)),
};
const projectedNft: ParserRecord<CardanoProjectedNft> = {
  ownerAddress: PaimaParser.NCharsParser(0, 1000),
  previousTxHash: PaimaParser.NCharsParser(0, 1000),
  previousOutputIndex: PaimaParser.NCharsParser(0, 1000),
  currentTxHash: PaimaParser.NCharsParser(0, 1000),
  currentOutputIndex: PaimaParser.NCharsParser(0, 1000),
  policyId: PaimaParser.NCharsParser(0, 1000),
  assetName: PaimaParser.NCharsParser(0, 1000),
  status: PaimaParser.NCharsParser(0, 1000),
};
const cardanoMint: ParserRecord<CardanoMint> = {
  txId: PaimaParser.NCharsParser(0, 64),
  metadata: PaimaParser.OptionalParser(null, PaimaParser.RegexParser(/[a-f0-9]*/)),
  assets: (keyName: string, input: string) => {
    return JSON.parse(input);
  },
};

const parserCommands: Record<string, ParserRecord<ParsedSubmittedInput>> = {
  createdLobby,
  joinedLobby,
  closedLobby,
  submittedMoves,
  zombieScheduledData,
  userScheduledData,
  scheduledBotMove,
  cardanoTransfer,
  cardanoDelegation,
  projectedNft,
  cardanoMint,
};

const myParser = new PaimaParser(myGrammar, parserCommands);

function parse(s: string): ParsedSubmittedInput {
  try {
    const parsed = myParser.start(s);
    return { input: parsed.command, ...parsed.args } as any;
  } catch (e) {
    console.log(e, 'Parsing error');
    return { input: 'invalidString' };
  }
}

export default parse;
