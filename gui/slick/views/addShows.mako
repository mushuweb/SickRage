<%inherit file="/layouts/main.mako"/>
<%!
    import os.path
    import urllib
    import sickbeard
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<div id="addShowPortal">
    <a href="${srRoot}/addShows/newShow/" id="btnNewShow" class="btn btn-large">
        <div class="button"><div class="add-list-icon-addnewshow"></div></div>
        <div class="buttontext">
            <h3>Add New Show</h3>
            <p>For shows that you haven't downloaded yet, this option finds a show on theTVDB.com, creates a directory for it's episodes, and adds it to Medusa.</p>
        </div>
    </a>
    <br /><br />

    <a href="${srRoot}/addShows/existingShows/" id="btnExistingShow" class="btn btn-large">
        <div class="button"><div class="add-list-icon-addexistingshow"></div></div>
        <div class="buttontext">
            <h3>Add Existing Shows</h3>
            <p>Use this option to add shows that already have a folder created on your hard drive. Medusa will scan your existing metadata/episodes and add the show accordingly.</p>
        </div>
    </a>
</div>
</%block>
