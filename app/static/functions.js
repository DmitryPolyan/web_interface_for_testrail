var emptySuite = true;
var notFullTestGroup = new Map();
//var notFullTestGroup = []
var parent_group_id;

// ф-я получения списка проекта или списка наборов тестов
function getLists(child_list) {
    notFullTestGroup = new Map() // Обнуление набора тестов при смене проекта или набора тестов
    let id;
    if (child_list == `#list_of_suites`) {
        id = $('#list_of_projects').val();
    } else if (child_list == `#list_of_sections`) {
        id = $('#list_of_suites').val()
    };
    $.ajax({
        url: '/get_from_db',
        type: 'get',
        data: {
            id: id
        },
        success: function(response) {
            $(child_list).children().remove();
            $(`#additional_list_of_section`).children().remove();
            $(`#list_of_sections`).children().remove();
            let i = 0;
            for (const [key, value] of Object.entries(response)) {
                if (child_list == `#list_of_suites`) {
                    $(child_list).append(`<option value="${key}">${value}</option>`);
                    getLists(`#list_of_sections`);
                } else if ((child_list == `#list_of_sections`) || (child_list = `#additional_list_of_section`)) {
                    i++;
                    if (i > (Object.keys(response).length / 2)) {
                        child_list = `#additional_list_of_section`
                    }
                    $(child_list).append(
                        `<div>
            <input type="checkbox" class="section_1" name="${value}" id_num="${key}">
            <label id="${key}" data-toggle="modal" data-target="#myModal" style="display: inline">${value}</label>
            </div>`
                    );
                };
            };
        },
        error: function(xhr) {
            alert('Some error')
        }
    });

}

// Удаление пустого значения в выборе проекта после первого выбора
function eraseEmpty() {
    $('option[value="-"]').remove();
    $('#list_of_projects').attr("onchange", "getLists(`#list_of_suites`)")
}

// Кнопка выделения/отмены всех тестов
function actionAll(action) {
    $('.section_1').each(function(i) {
        $(this).prop("checked", action);
        $(`#${Number($(this).attr("id_num"))}`).css("color", "black");
    });
    if (!action){
        notFullTestGroup = new Map(); // Обнуление набора тестов при смене проекта или набора тестов
        }
};


//ф-я указания пути к исполняемому файлу
function changePath() {
    $.ajax({
        url: '/change_path',
        type: 'get',
        success: function(response) {
            if (response != 'CANCELED') {
                $(`#pathToMain`)[0].outerText = response
            };
        },
    });
};

// Обработка нажатия кнопки "Режим редактирования"
function editProfile() {
    document.getElementById('editProfileButton').style = "display:none";
    cleaningFields();
    document.getElementById('username').oninput = dataValidation;
    $('#select_user').children().remove();
    $('#userList').attr('style', '')
    $('#submit').val('Изменить');
    $('#edition_buttons').children().remove();
    $('#edition_buttons').append(`
  <p></p>
  <input type='button' onclick='cancelEdition()' value='Отмена редактирования'>
  `)
    $('#del_button').append(`
  <p></p>
  <input type='button' onclick='deleteUser()' value='Удалить выбранного пользователя'>
  `)
    $.ajax({
        url: '/get_users',
        type: 'get',
        success: function(response) {
            for (const [key, value] of Object.entries(response)) {
                if (value != 'guest') {
                    $('#select_user').append(`<option id=${key}>${value}</option>`)
                }
            };
        },
        error: function(response) {
            console.log(response)
        },
    });
};


//ф-я вызова проверки существования имени при редактировании
function dataValidation() {
    if (($('#select_user').val() == $('#username').val()) || userNotExist()) {
        $('label:first').text('Username');
        $('label:first').css('color', 'black');
        $('#submit').prop('disabled', false)
    } else {
        $('label:first').text('Данное имя уже используется');
        $('label:first').css('color', 'red');
        $('#submit').prop('disabled', true);
    }
};

// Возвращает true если пользователь не существует в списке при редактировании
function userNotExist() {
    let uL = $('#select_user option').map(function() {
        return this.value;
    }).get().join();
    uL = uL.split(',');
    let userInList;
    if ($('#username').val() == '') {
        userInList = true
    } else {
        userInList = (uL.indexOf($('#username').val()) == -1);
    };
    return userInList;
}

// Ф-я заполнения полей при редактировании пользователей
function getUserInformation() {
    $.ajax({
        url: '/get_user_information',
        type: 'get',
        data: {
            chosenUser: $('#select_user').val()
        },
        success: function(response) {
            $('#username').val(response.name);
            $('#email').val(response.email);
            $('#password').val(response.password);
            $('#password2').val(response.password);
            $('#role').val(response.role);
        },
        error: function() {
            alert('Something wrong')
        },
    })
}

// Отмена редактирования, выход из режима редактирования
function cancelEdition() {
    let cancel = confirm('Вы действительно хотите выйти из режима редактирования?');
    if (cancel) {
        location.reload();
        cleaningFields();
    }
}

// Очистка полей при смене режима создания и редактирования
function cleaningFields() {
    $('#username').val('');
    $('#email').val('');
    $('#password').val('');
    $('#password2').val('');
    $('#role').val('user')
}

// ф-я удаления выбранного пользователя
function deleteUser() {
    let delUser = confirm('Вы действительно хотите удалить пользователя?');
    if (delUser) {
        $.ajax({
            url: '/del_user',
            type: 'get',
            data: {
                chosenUser: $('#select_user').val()
            },
            success: function(response) {
                alert(response);
                cleaningFields();
                location.reload()
            }
        })
    }
}

$('#myModal').on('show.bs.modal', function(e) {
    let $modal = $(this),
        groupsId = e.relatedTarget.id;
    if (e.relatedTarget.value == "Запустить выбранные тесты") {
        $modal.find('.edit-content').html('');
        $('.section_1').each(function() {
            if ($(this).prop('checked') == true) {
                $modal.find('.edit-content').append(`
            <div><input type="number" class = "mod_numbers" id ="${$(this).attr('name')}" id_num="${$(this).attr('id_num')}" min="0" max="9" value=1 size="3">${$(this).attr('name')}</div>
            `);
            };
            $modal.find('.edit-header').html("Введите кол-во запусков");
            $modal.find('.btn-primary').attr("onclick", "getTestsNumber()")
        });
    } else {
        $.ajax({
            cache: false,
            type: 'GET',
            url: '/get_from_db',
            data: {
                id: groupsId
            },
            success: function(response) {
                let name_group = e.relatedTarget.innerHTML;
                parent_group_id = Number(e.relatedTarget.id);
                $modal.find('.edit-content').html('');
                for (const [key, value] of Object.entries(response)) {
                    $modal.find('.edit-content').append(`<div>
            <input type="checkbox"  class="mod_checkbox" name="${value}" id_num="${key}">
            <label style="display: inline">${value}</label>
            </div>`)
                };
                $modal.find('.edit-header').html(name_group);
                $modal.find('.btn-primary').attr("onclick", "getCheckedTests()");

                if (notFullTestGroup.has(name_group)) {
                    for (let i = 0; i < notFullTestGroup.get(name_group)['tests'].length; i++) {
                        $(`[id_num="${notFullTestGroup.get(name_group)['tests'][i][1]}"]`).prop('checked', true)
                    }
                };

            }
        })
    };
})

// Получение колличества тестов и запуск (в данный момент просто создание json в корне)
function getTestsNumber() {
    $('.mod_numbers').each(function() {
        if ($(this).val() > 0) {
            if (notFullTestGroup.has($(this).attr('id'))) {
                notFullTestGroup.get($(this).attr('id'))['count'] = $(this).val()
            } else {
                notFullTestGroup.set($(this).attr('id'), {
                    tests: [],
                    groupId: Number($(this).attr('id_num')),
                    count: $(this).val(),
                    full_group: true
                });
            }
        } else {
            notFullTestGroup.delete($(this).attr('id'))
        }
    });
    Map.prototype.toJSON = function () {return JSON.stringify([...this]);};
    notFullTestGroup.set('project_id', $('#list_of_projects').val());
    notFullTestGroup.set('suite_id', $('#list_of_suites').val());
    $.ajax({
            type: 'POST',
            url: '/json_result',
            data: {
                jsonFile: notFullTestGroup.toJSON(),
            },
            dataType: "json",
            success: function(response) { alert(response)}
});
$('.modal').modal('hide');
}


function getCheckedTests() {
    let checked_tests = [];
    let name_group = $('#myModalLabel').text();
    $('.mod_checkbox').each(function() {
        if ($(this).prop('checked') == true) {
            checked_tests.push([$(this).attr('name'), Number($(this).attr('id_num'))])
        }
    });
    if (checked_tests.length > 0) {
        //checked_tests.push(parent_group_id); //Добавляем в конец ид группы, из которой взяты тесты
        //notFullTestGroup.set(name_group, checked_tests);
        notFullTestGroup.set(name_group, {
            tests: checked_tests,
            groupId: Number(parent_group_id),
            count: 1,
            full_group: false
        });
        $(`[id_num="${parent_group_id}"]`).prop('checked', true);
        $(`#${parent_group_id}`).css('color', 'blue'); //Выделяем неполную группу синим цветом
        $(`[id_num="${parent_group_id}"]`).click(function() {
            $(`#${parent_group_id}`).css('color', 'black');
            notFullTestGroup.delete(name_group);
            $(`[id_num="${parent_group_id}"]`).click(function() {});
        })
    }
    $('.modal').modal('hide');
};

//Обработчик включения/выключения плагинов
$('ul#plugin_checkbox .chkbox').on('change', function() {
            let action;
            if ($(this).prop('checked')) {
                action = 'add';
            } else {
                action = 'del';
            };
            $.ajax({
            type: 'POST',
            url: '/on_off_plugin',
            data: {
                plugin: $(this).prop('name'),
                action: action
            }
});
})

//Кнопка открытия модального окна с настройками плагина
$('#pluginsModal').on('show.bs.modal', function(e) {
    var $modal = $(this),
        pluginId = e.relatedTarget.id;
    $modal.find('.edit-content').html('');
    $.ajax({
        type: 'GET',
        url: '/get_json_plugin_config',
        data: {
            pluginId: pluginId
        },
        success: function(response) {
            $modal.find('.edit-content').append(`<h1 id='pluginsName'>${pluginId}</h1>`);
            for (const [key, value] of Object.entries(response)) {
                if (key != 'description') {
                    let str = value.replace(/"/g, '&quot;');
                    $modal.find('.edit-content').append(
                        `<p>${key} - <input type="text" id="${key}" value="`+ str +`" class="plugin_prop" size="40"></p>`
                    );
                }
            };
            $modal.find('.btn-primary').attr("onclick", "pluginsConfigSave(" + pluginId + ")");
            $modal.find('.btn-warning').attr("onclick", "pluginsDefaultSettings(" + pluginId + ")");
        },
    });
})

//Обработка нажатия кнопки сохранения настрек плагина
function pluginsConfigSave(pluginId) {
    let change = 0; // Индикатор изменений в настройках плагина
    let newJson = new Object();
    $('.plugin_prop').each(function() {
        if ($(this).val() != $(this).attr('value')) {
            change = 1;
            newJson[$(this).attr('id')] = $(this).val();
        };
    });
    let saveSettings = confirm("Сохранить изменения?");
    if (saveSettings) {
        if (change) {
            $.ajax({
                type: 'POST',
                url: '/plugin_config_update',
                data: {
                    jsonFile: JSON.stringify(newJson),
                    plugin_name: pluginId.id
                },
                success: function(msg) {
                alert('Настройки сохранены!')
                },
                error: function(err){
                console.log(err);
                }
            });
            $('.modal').modal('hide');
        } else {
            alert('Изменений не обнаружено');
        };
    }
}

// Обработка наатия кнопки восстановления настроек по умолчанию
function pluginsDefaultSettings(pluginId) {
    var defaultSettings = confirm("Загрузить настройки по умолчанию?");
    if (defaultSettings) {
        $.ajax({
            type: 'POST',
            url: '/pluginsDefaultLoad',
            data: {
                name_plugin: pluginId.id
            },
            success: function(response) {
                if (response == 'True') {
                    alert('Настройки по умолчанию восстановлены');
                } else {
                    alert('Не удалось восстановить значения по умолчанию');
                };
                $('.modal').modal('hide');
            }
        });
    };
}

function checkUpdateDB() {
    $.ajax({
        type: 'GET',
        url: '/get_status_db',
        success: function(response) {
            let response_obj = JSON.parse(response);
            if (response_obj.db_status) {
                $('#dbStatus').text('БД Testrail была обновлена. Последнее обновление: ' + response_obj.date_update)
            } else {
                $('#dbStatus').text('БД Testrail не была обновлена. Последнее обновление: ' + response_obj.date_update);
                $('#dbStatus').css('color', 'red');
            }
        }
    });
}

