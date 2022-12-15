"""Block header store.

"""
import abc
import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pandas as pd


@dataclass(slots=True, frozen=True)
class BlockHeader:
    """Describe block headers for a single block."""

    #: 32-bit uint of he block number
    block_number: int

    #: Block hash as 0x prefixed string
    #:
    #: Note that this might be converted to binary data later.
    block_hash: str

    #: 32 bit uint UNIX UTC timestamp of the block
    timestamp: int

    def __post_init__(self):
        assert type(self.block_number) == int
        assert type(self.block_hash) == str
        assert type(self.timestamp) == int
        assert self.block_hash.startswith("0x")

    @staticmethod
    def generate_headers(count: int,
                         start_block: int = 1,
                         start_time: float = 0,
                         blocks_per_second: float = 12) -> Dict[str, list]:
        """Generate random block header data.

        Used for testing.


        :return:
            DataFrame indexed by block number
        """

        # Columnar data
        block_number = []
        block_hash = []
        timestamp = []

        clock = start_time
        for i in range(start_block, start_block + count):
            block_number.append(i)
            block_hash.append(hex(random.randint(2 ** 31, 2 ** 32)))
            timestamp.append(int(clock))
            clock += blocks_per_second

        return {
            "block_number": block_number,
            "block_hash": block_hash,
            "timestamp": timestamp,
        }

    @staticmethod
    def to_pandas(headers: Dict[str, list], partitioning_size: Optional[int]=None):
        """Convert columnar header data to Pandas.

        .. note ::

            Depends on Pandas, but because we have optional dependency do a lazy import.

        :param headers:
            Raw block data to write.

        :param partitioning_size:
            Create a key "partition" which each contains partitioning_size blocks.
            E.g. 100_000.

        :return:
        """
        import pandas as pd
        # https://stackoverflow.com/a/64537577/315168
        df = pd.DataFrame.from_dict(headers, orient='columns')
        if partitioning_size:
            assert partitioning_size > 0
            df["partition"] = df["block_number"].apply(lambda x: (x // partitioning_size) * partitioning_size)
        return df


class BlockHeaderStore(abc.ABC):
    """Block headers persistent storage interface.

    Cache downlaoded block headers and timestamps,
    so you do not need to fetch them again over JSON-RPC when restarting an application.

    Block header is a tuple

    - block number (int 32)
    - block header (bytes 32)
    - UNIX UTC timestamp (uint 32)

    Block header store can support partial writes (Parquet datasets).
    In this case, you want to usually rewrite two of the latest partion keys
    if you are adding data incrementaly, as there might be minor chain reoganisations
    e.g. across date boundaries.
    """

    def load(self, since_block_number: int = 0) -> pd.DataFrame:
        """Load data from the store.

        :param since_block_number:
            Return only blocks after this (inclusive)

        :return:
        """

    def save(self, data: pd.DataFrame):
        """Save to the store."""

    def save_incremental(self, data: pd.DataFrame) -> Tuple[int, int]:
        """Save the latest data to the store.

        Write the minimum amount of data to the disk we think is

        - Valid

        - Needs to be written to keep partitions intact

        :return:
            Block range written (inclusive)
        """