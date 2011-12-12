Please add notes about new features, bug fixing, and other things at the end of the list.
===============================================================================
NEW FEATURES
===============================================================================

1.
Image rotation during uploading, according to exif:Orientation (issue 12)

2.
Manual images rotation from NotreDAM application Edit menu.

3.
Stop all in script menu to stop all pending processes.

===============================================================================
BUG FIXING
===============================================================================

1.
Fixed the wellknown bug in the user preferences window (issue 41)
2.
Sorted the list of members available in
Workspace->Configure->Members in case of 'Add member'
3.
Fixed the bug in DAMComponentSetting, when two SettingValue related to 
different DAMComponentSetting had the same name (issue 45).
4.
Fixed a bug in xmp_embedding, now it works again (issue 47)
5.
Fixed problem in uploading of many files when one of them fails. Now uploading completes successfully for all on the application side, but the notification window worns about the number of failed uploading (issue 44).
6.
Fixed the bug in google map loading when a proper GOOGLE_KEY is missing.
A proper GOOGLE_KEY is still required, but now the user is informed about it and
the application does not remain loading until the refresh is called in the browser.
 
===============================================================================
OTHER THINGS
===============================================================================

1.
Added 404.html and 500.html templates, but remember to set DEBUG to false in
settings.py otherwise the error page will appear anycase.


