========
Progress
========

- Aug 20:

    - `CREATE` is working for Domain, MailingList, Membership models
      at both rest and core layers.

    - Pulling up Related models:
        - Handling related adaptors that **are** remotely backed up in `post_save`
   
        - Related models that **are not** remotely backed up (like Email) raise an exception as of now. 
          This should be handled in a different manner.

        - Regarding that point, `Email` is something which is not allowed creation/updation at Core.
          Fix that plox. :(

    - Some docs re: preferences. Do we need to address their premissions at our
      own level as well? (System prefs etc are read-only, while others can be modified)

    - Currently working on `filter` (and by extension, `get`).

    - Pain point: The whole process of `sanitizing` data is spread all over the
      place in `interface.py` and `api.py`. Should get on fixing that as well.
