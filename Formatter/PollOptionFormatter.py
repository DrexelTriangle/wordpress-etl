from Formatter.PollFormatter import PollFormatter


class PollOptionFormatter(PollFormatter):
    """Writes the poll options table, including the preserved vote counts.

    Vote counts are the reason the archive is seeded as SQL rather than posted
    through the API: POST /v1/polls has no field for them, so an API import
    would create every poll with its results reading zero.
    """

    CMS_COLUMNS = [
        "id",
        "poll_id",
        "option_name",
        "vote_count",
        "sort_order",
    ]
    CMS_SCHEMA = {
        "id": "BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "poll_id": "BIGINT NOT NULL",
        "option_name": "VARCHAR(128) NOT NULL",
        "vote_count": "BIGINT UNSIGNED NOT NULL DEFAULT 0",
        "sort_order": "INT NOT NULL DEFAULT 0",
        "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }
    CMS_DEFAULTED_COLUMNS = ["created_at"]
    # The unique key is what makes a re-seed safe to reason about, and the
    # cascade is what keeps deleting a poll from stranding its options.
    CMS_INDEXES = [
        "UNIQUE KEY uq_cms_poll_options_poll_name (poll_id, option_name)",
        "INDEX idx_cms_poll_options_poll_sort (poll_id, sort_order, id)",
        "CONSTRAINT fk_cms_poll_options_poll "
        "FOREIGN KEY (poll_id) REFERENCES cms_polls (id) ON DELETE CASCADE",
    ]
    FIELD_MAP = {
        "id": "id",
        "poll_id": "pollID",
        "option_name": "optionName",
        "vote_count": "voteCount",
        "sort_order": "sortOrder",
    }

    def iter_format(self, table="cms_poll_options"):
        yield from super().iter_format(table)

    def format(self, table="cms_poll_options"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
