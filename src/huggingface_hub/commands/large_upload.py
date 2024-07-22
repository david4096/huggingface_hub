# coding=utf-8
# Copyright 2023-present, the HuggingFace Inc. team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains command to upload a large folder with the CLI."""

import os
from argparse import Namespace, _SubParsersAction
from typing import List, Optional

from huggingface_hub import logging
from huggingface_hub.commands import BaseHuggingfaceCLICommand
from huggingface_hub.hf_api import HfApi
from huggingface_hub.utils import disable_progress_bars

from ._cli_utils import ANSI


logger = logging.get_logger(__name__)


class LargeUploadCommand(BaseHuggingfaceCLICommand):
    @staticmethod
    def register_subcommand(parser: _SubParsersAction):
        large_upload_parser = parser.add_parser(
            "large-upload", help="Upload a large folder folder to a repo on the Hub"
        )
        large_upload_parser.add_argument(
            "repo_id", type=str, help="The ID of the repo to upload to (e.g. `username/repo-name`)."
        )
        large_upload_parser.add_argument("local_path", type=str, help="Local path to the file or folder to upload.")
        large_upload_parser.add_argument(
            "--repo-type",
            choices=["model", "dataset", "space"],
            help="Type of the repo to upload to (e.g. `dataset`).",
        )
        large_upload_parser.add_argument(
            "--revision",
            type=str,
            help=("An optional Git revision to push to. It can be a branch name or a PR reference."),
        )
        large_upload_parser.add_argument(
            "--private",
            action="store_true",
            help=(
                "Whether to create a private repo if repo doesn't exist on the Hub. Ignored if the repo already exists."
            ),
        )
        large_upload_parser.add_argument(
            "--include", nargs="*", type=str, help="Glob patterns to match files to upload."
        )
        large_upload_parser.add_argument(
            "--exclude", nargs="*", type=str, help="Glob patterns to exclude from files to upload."
        )
        large_upload_parser.add_argument(
            "--token", type=str, help="A User Access Token generated from https://huggingface.co/settings/tokens"
        )
        large_upload_parser.add_argument(
            "--num-workers", type=int, help="Number of workers to use to hash, upload and commit files."
        )
        large_upload_parser.add_argument(
            "--no-report", action="store_true", help="Whether to regularly print a status report."
        )
        large_upload_parser.add_argument("--no-bars", action="store_true", help="Whether to disable progress bars.")
        large_upload_parser.set_defaults(func=LargeUploadCommand)

    def __init__(self, args: Namespace) -> None:
        self.repo_id: str = args.repo_id
        self.local_path: str = args.local_path
        self.repo_type: str = args.repo_type
        self.revision: Optional[str] = args.revision
        self.private: bool = args.private

        self.include: Optional[List[str]] = args.include
        self.exclude: Optional[List[str]] = args.exclude

        self.api: HfApi = HfApi(token=args.token, library_name="huggingface-cli")

        self.num_workers: Optional[int] = args.num_workers
        self.no_report: bool = args.no_report
        self.no_bars: bool = args.no_bars

        if not os.path.isdir(self.local_path):
            raise ValueError("Large upload is only supported for folders.")

    def run(self) -> None:
        logging.set_verbosity_info()

        print(
            ANSI.yellow(
                "You are about to upload a large folder to the Hub using `huggingface-cli large-upload`.\n"
                "Please remember that this is still experimental so expect some rough edges in the process.\n\n"
                "A few things to keep in mind:\n"
                "- Repository limits still apply: https://huggingface.co/docs/hub/repositories-recommendations\n"
                "- Do not start several processes in parallel.\n"
                "- You can interrupt and resume the process at any time. "
                "The script will pick up where it left off except for partially uploaded files that would have to be entirely reuploaded.\n"
                f"- Some metadata will be stored under `{self.local_path}/.huggingface`.\n"
                "  - You must not modify those files manually.\n"
                "  - You must not delete the `.huggingface/` folder while a process is running.\n"
                "  - You can delete the `.huggingface/` folder to reinitialize the upload state (when not running). Files will have to be hashed and preuploaded again, except for already committed files.\n"
                "- Do not upload the same folder to several repositories. If you need to do so, you must delete the `.huggingface/` folder first.\n"
                "For more details about available options, run `huggingface-cli large-upload --help`.\n"
                "\n"
                "Feedback is very welcome! Don't forget to report back how it went on https://github.com/huggingface/huggingface_hub/pull/2254"
            )
        )

        if self.no_bars:
            disable_progress_bars()

        self.api.large_upload(
            repo_id=self.repo_id,
            folder_path=self.local_path,
            repo_type=self.repo_type,
            revision=self.revision,
            private=self.private,
            allow_patterns=self.include,
            ignore_patterns=self.exclude,
            num_workers=self.num_workers,
            print_report=not self.no_report,
        )
