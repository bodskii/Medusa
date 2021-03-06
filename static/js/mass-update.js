$(document).ready(function() {
    $('.submitMassEdit').on('click', function() {
        var editArr = [];

        $('.editCheck').each(function() {
            if (this.checked === true) {
                editArr.push($(this).attr('id').split('-')[1]);
            }
        });

        if (editArr.length === 0) {
            return;
        }

        window.location.href = $('base').attr('href') + 'manage/massEdit?toEdit=' + editArr.join('|');
    });

    $('.submitMassUpdate').on('click', function() {
        var updateArr = [];
        var refreshArr = [];
        var renameArr = [];
        var subtitleArr = [];
        var deleteArr = [];
        var removeArr = [];
        var metadataArr = [];

        $('.updateCheck').each(function() {
            if (this.checked === true) {
                updateArr.push($(this).attr('id').split('-')[1]);
            }
        });

        $('.refreshCheck').each(function() {
            if (this.checked === true) {
                refreshArr.push($(this).attr('id').split('-')[1]);
            }
        });

        $('.renameCheck').each(function() {
            if (this.checked === true) {
                renameArr.push($(this).attr('id').split('-')[1]);
            }
        });

        $('.subtitleCheck').each(function() {
            if (this.checked === true) {
                subtitleArr.push($(this).attr('id').split('-')[1]);
            }
        });

        $('.removeCheck').each(function() {
            if (this.checked === true) {
                removeArr.push($(this).attr('id').split('-')[1]);
            }
        });

        var deleteCount = 0;

        $('.deleteCheck').each(function() {
            if (this.checked === true) {
                deleteCount++;
            }
        });

        var totalCount = [].concat.apply([], [updateArr, refreshArr, renameArr, subtitleArr, deleteArr, removeArr, metadataArr]).length; // eslint-disable-line no-useless-call

        if (deleteCount >= 1) {
            $.confirm({
                title: 'Delete Shows',
                text: 'You have selected to delete ' + deleteCount + ' show(s).  Are you sure you wish to continue? All files will be removed from your system.',
                confirmButton: 'Yes',
                cancelButton: 'Cancel',
                dialogClass: 'modal-dialog',
                post: false,
                confirm: function() {
                    $('.deleteCheck').each(function() {
                        if (this.checked === true) {
                            deleteArr.push($(this).attr('id').split('-')[1]);
                        }
                    });
                    if (totalCount === 0) {
                        return false;
                    }
                    var params = $.param({
                        toUpdate: updateArr.join('|'),
                        toRefresh: refreshArr.join('|'),
                        toRename: renameArr.join('|'),
                        toSubtitle: subtitleArr.join('|'),
                        toDelete: deleteArr.join('|'),
                        toRemove: removeArr.join('|'),
                        toMetadata: metadataArr.join('|')
                    });

                    window.location.href = $('base').attr('href') + 'manage/massUpdate?' + params;
                }
            });
        }
        if (totalCount === 0) {
            return false;
        }
        var params = $.param({
            toUpdate: updateArr.join('|'),
            toRefresh: refreshArr.join('|'),
            toRename: renameArr.join('|'),
            toSubtitle: subtitleArr.join('|'),
            toDelete: deleteArr.join('|'),
            toRemove: removeArr.join('|'),
            toMetadata: metadataArr.join('|')
        });
        window.location.href = $('base').attr('href') + 'manage/massUpdate?' + params;
    });

    ['.editCheck', '.updateCheck', '.refreshCheck', '.renameCheck', '.deleteCheck', '.removeCheck'].forEach(function(name) {
        var lastCheck = null;

        $(name).on('click', function(event) {
            if (!lastCheck || !event.shiftKey) {
                lastCheck = this;
                return;
            }

            var check = this;
            var found = 0;

            $(name).each(function() {
                if (found === 1) {
                    if (!this.disabled) {
                        this.checked = lastCheck.checked;
                    }
                }
                if (found === 2) {
                    return false;
                }
                if (this === check || this === lastCheck) {
                    found++;
                }
            });
        });
    });
});
