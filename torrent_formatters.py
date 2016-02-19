from typing import Iterable, List

from models import DownloadInfo, TorrentInfo
from utils import humanize_size, humanize_speed


COLUMN_WIDTH = 30
INDENT_WIDTH = 4
PROGRESS_BAR_WIDTH = 50


def join_lines(lines: Iterable[str]) -> str:
    return ''.join(line[:-1].ljust(COLUMN_WIDTH) if line.endswith('\t') else line for line in lines)


def format_title(torrent_info: TorrentInfo) -> List[str]:
    download_info = torrent_info.download_info  # type: DownloadInfo
    lines = ['Name: {}\n'.format(download_info.suggested_name),
             'ID: {}\n'.format(download_info.info_hash.hex())]
    return lines


def format_content(torrent_info: TorrentInfo) -> List[str]:
    download_info = torrent_info.download_info  # type: DownloadInfo

    lines = ['Announce URL: {}\n'.format(torrent_info.announce_url)]

    single_file_mode = (len(download_info.files) == 1 and not download_info.files[0].path)
    total_size_repr = humanize_size(download_info.total_size)
    if single_file_mode:
        lines.append('Content: single file ({})\n'.format(total_size_repr))
    else:
        lines.append('Content: {} files (total {})\n'.format(len(download_info.files), total_size_repr))
        for file_info in download_info.files:
            lines.append(' ' * INDENT_WIDTH + '{} ({})\n'.format(
                '/'.join(file_info.path), humanize_size(file_info.length)))
    return lines


def format_status(torrent_info: TorrentInfo) -> List[str]:
    download_info = torrent_info.download_info  # type: DownloadInfo
    statistics = download_info.session_statistics
    lines = []

    selected_files_count = sum(1 for info in download_info.files if info.selected)
    selected_piece_count = sum(1 for info in download_info.pieces if info.selected)
    lines.append('Selected: {}/{} files ({}/{} pieces)\n'.format(
        selected_files_count, len(download_info.files), selected_piece_count, download_info.piece_count))
    lines.append('Directory: {}\n'.format(torrent_info.download_dir))

    if torrent_info.paused:
        state = 'Paused'
    elif download_info.complete:
        state = 'Uploading'
    else:
        state = 'Downloading'
    lines.append('State: {}\n'.format(state))

    lines.append('Download from: {}/{} peers\t'.format(statistics.downloading_peer_count, statistics.peer_count))
    lines.append('Upload to: {}/{} peers\n'.format(statistics.uploading_peer_count, statistics.peer_count))

    lines.append('Download speed: {}\t'.format(
        humanize_speed(statistics.download_speed) if statistics.download_speed is not None else 'unknown'))
    lines.append('Upload speed: {}\n'.format(
        humanize_speed(statistics.upload_speed) if statistics.upload_speed is not None else 'unknown'))

    last_piece_info = download_info.pieces[-1]
    downloaded_size = download_info.downloaded_piece_count * download_info.piece_length
    if last_piece_info.downloaded:
        downloaded_size += last_piece_info.length - download_info.piece_length
    selected_size = selected_piece_count * download_info.piece_length
    if last_piece_info.selected:
        selected_size += last_piece_info.length - download_info.piece_length
    lines.append('Size: {}/{}\t'.format(humanize_size(downloaded_size), humanize_size(selected_size)))

    ratio = statistics.total_uploaded / statistics.total_downloaded if statistics.total_downloaded else 0
    lines.append('Ratio: {:.1f}\n'.format(ratio))

    progress = downloaded_size / selected_size
    progress_bar = ('#' * round(progress * PROGRESS_BAR_WIDTH)).ljust(PROGRESS_BAR_WIDTH)
    lines.append('Progress: {:5.1f}% [{}]\n'.format(progress * 100, progress_bar))

    return lines