import json
import logging
import urllib
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from .utils import api_post, user_can_edit_demo

logger = logging.getLogger(__name__)


@login_required(login_url="login")
def homepage(request):
    qfilter = request.GET.get("qfilter", "")
    try:
        page = request.GET.get("page")
        page = int(page)
    except Exception:
        page = 1

    settings = {"num_elements_page": 100, "page": page, "qfilter": qfilter}
    demos, _ = api_post(
        "/api/demoinfo/demo_list_pagination_and_filter", method="get", params=settings
    )

    # display the editor's demos
    if page == 1 and not qfilter:
        editor_info, _ = api_post(
            "/api/demoinfo/editor",
            "get",
            params={"email": request.user.email},
        )
        editorid = editor_info["editor"]["id"]
        own_demos, _ = api_post(
            f"/api/demoinfo/demo_list_by_editorid/{editorid}", method="get"
        )
    else:
        own_demos = []

    context = {
        "demos": demos["demo_list"],
        "own_demos": own_demos,
        "page": page,
        "next_page_number": demos["next_page_number"],
        "previous_page_number": demos["previous_page_number"],
        "qfilter": qfilter,
    }
    return render(request, "homepage.html", context)


@login_required(login_url="login")
@csrf_protect
def status(request):
    return render(request, "status.html")


@login_required(login_url="login")
def demo_editors(request):
    demo_id = request.GET["demo_id"]

    editor_list, _ = api_post(f"/api/demoinfo/demos/{demo_id}/editors", method="get")
    available_editors, _ = api_post(
        f"/api/demoinfo/available_editors/{demo_id}", method="get"
    )
    available_editors = sorted(available_editors, key=lambda e: e["name"])

    can_edit = user_can_edit_demo(request.user, demo_id)

    context = {
        "demo_id": demo_id,
        "can_edit": can_edit,
        "editors_list": editor_list,
        "available_editors": available_editors,
    }

    return render(request, "demoEditors.html", context)


@login_required(login_url="login")
def add_demo_editor(request):
    demo_id = request.POST["demo_id"]
    editor_id = request.POST["editor_id"]
    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response, status = api_post(
            f"/api/demoinfo/demos/{demo_id}/editor/{editor_id}", method="post"
        )

    response = {}
    if status != 201:
        response["status"] = "KO"
        response["message"] = demoinfo_response.get("error")
        return HttpResponse(json.dumps(response), "application/json")
    else:
        return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required(login_url="login")
def reset_ssh_key(request):
    demo_id = request.POST["demo_id"]
    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response, status = api_post(
            f"/api/demoinfo/reset_ssh_keys/{demo_id}", method="get"
        )

    response = {}
    if status != 200:
        response["status"] = "KO"
        response["message"] = demoinfo_response.get("error")
        return HttpResponse(json.dumps(response), "application/json")
    else:
        return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required(login_url="login")
def remove_demo_editor(request):
    demo_id = request.POST["demo_id"]
    editor_id = request.POST["editor_id"]
    if user_can_edit_demo(request.user, demo_id):
        demoinfo_response, status = api_post(
            f"/api/demoinfo/demos/{demo_id}/editor/{editor_id}", method="delete"
        )

    response = {}
    if status != 204:
        response["status"] = "KO"
        response["message"] = demoinfo_response.get("error")
        return HttpResponse(json.dumps(response), "application/json")
    else:
        response["status"] = "OK"
        return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
@csrf_protect
def ajax_add_demo(request):
    state = request.POST["state"].lower()
    title = request.POST["title"]
    demo_id = request.POST["demo_id"]

    try:
        demo_id = int(demo_id)
    except ValueError:
        return JsonResponse(
            {"status": "KO", "message": "The demo ID should be an integer."}, status=400
        )

    settings = {"state": state, "title": title, "demo_id": demo_id, "ddl": "{}"}
    result, demo_status = api_post("/api/demoinfo/demo", method="post", params=settings)

    response = {}
    if demo_status != 201:
        messages.warning(request, "This demo ID is already taken")
        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    editor_info, _ = api_post(
        "/api/demoinfo/editor", method="get", params={"email": request.user.email}
    )
    editor_id = editor_info["editor"]["id"]
    _, editor_status = api_post(
        f"/api/demoinfo/demos/{demo_id}/editor/{editor_id}", method="post"
    )

    if editor_status != 201:
        response["status"] = "KO"
        response["message"] = result.get("error")
        return JsonResponse(
            {"status": "KO", "message": response["message"]}, status=400
        )
    else:
        response["status"] = "OK"
        return HttpResponseRedirect(f"/cp2/showDemo?demo_id={demo_id}")


@login_required(login_url="login")
@csrf_protect
def ajax_delete_demo(request):
    demo_id = request.POST["demo_id"]

    if user_can_edit_demo(request.user, demo_id):
        result, status = api_post(f"/api/core/demo/{demo_id}", method="delete")

    response = {}
    if status != 204:
        result = result.json()
        response["status"] = "KO"
        response["message"] = result.get("detail").get("error")
    else:
        response["status"] = "OK"
    return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
def templates(request):
    templates, _ = api_post("/api/blobs/templates", "get")
    context = {"templates": templates}
    return render(request, "Templates.html", context)


@login_required(login_url="login")
@csrf_protect
def ajax_add_template(request):
    template_name = request.POST["templateName"]
    settings = {"template_name": template_name}
    result, response_code = api_post(
        "/api/blobs/templates", method="post", params=settings
    )

    if response_code == 201:
        return JsonResponse({"template_id": result["template_id"]}, status=200)
    else:
        return JsonResponse({"message": "Unauthorized"}, status=401)


@login_required(login_url="login")
@never_cache
def showTemplate(request):
    template_id = request.GET["template_id"]
    template_name = request.GET["template_name"]

    template_sets, _ = api_post(f"/api/blobs/templates/{template_id}", method="get")

    demos_using_template, _ = api_post(
        f"/api/blobs/demos_using_template/{template_id}",
        method="get",
    )
    can_edit = request.user.is_superuser
    context = {
        "template_id": template_id,
        "template_name": template_name,
        "template_sets": template_sets,
        "demos_using_template": demos_using_template,
        "can_edit": can_edit,
    }
    return render(request, "showTemplate.html", context)


@login_required(login_url="login")
def ajax_delete_template(request):
    template_id = request.POST["template_id"]
    response = {}
    _, response_code = api_post(f"/api/blobs/templates/{template_id}", method="delete")

    if response_code != 204:
        response["status"] = "KO"
    else:
        response["status"] = "OK"
    return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
def ajax_remove_blob_from_template(request):
    template_id = request.POST["template_id"]
    blob_set = request.POST["blob_set"]
    pos_set = request.POST["pos_set"]

    settings = {"template_id": template_id, "blob_set": blob_set, "pos_set": pos_set}
    _, status_code = api_post(
        f"/api/blobs/template_blobs/{template_id}", method="delete", params=settings
    )
    if status_code == 201:
        return HttpResponse(json.dumps({"status": "OK"}), "application/json")
    else:
        return HttpResponse(json.dumps({"status": "KO"}), "application/json")


@login_required(login_url="login")
def ajax_remove_blob_from_demo(request):
    demo_id = request.POST["demo_id"]
    blob_set = request.POST["blob_set"]
    pos_set = request.POST["pos_set"]

    if not user_can_edit_demo(request.user, demo_id):
        response = {}
        response["status"] = "KO"
        response["message"] = "User not allowed"
        return HttpResponse(json.dumps(response), "application/json")

    settings = {"blob_set": blob_set, "pos_set": pos_set}
    response, status_code = api_post(
        f"/api/blobs/demo_blobs/{demo_id}", method="delete", params=settings
    )
    if status_code == 204:
        return HttpResponse(json.dumps({"status": "OK"}), "application/json")
    else:
        return HttpResponse(json.dumps({"status": "KO"}), "application/json")


@login_required(login_url="login")
def CreateBlob(request):
    context = {}
    if "demo_id" in request.GET:  # demo blob edit
        can_edit = user_can_edit_demo(request.user, request.GET["demo_id"])
        context = {
            "create_blob": True,
            "demo_id": request.GET["demo_id"],
            "can_edit": can_edit,
        }
    else:  # Template blob edit
        template_id = request.GET["template_id"]
        template_name = request.GET["template_name"]
        context = {
            "create_blob": True,
            "template_id": template_id,
            "template_name": template_name,
        }
    return render(request, "createBlob.html", context)


@login_required(login_url="login")
def ajax_add_blob_demo(request):
    blob_set = request.POST["SET"]
    pos_set = request.POST["PositionSet"]
    title = request.POST["Title"]
    credit = request.POST["Credit"]
    demo_id = request.POST["demo_id"]
    files = {"blob": request.FILES["Blobs"].file}
    if "VR" in request.FILES:
        files["blob_vr"] = request.FILES["VR"].file

    response = {}
    if not user_can_edit_demo(request.user, demo_id):
        return render(request, "homepage.html")

    settings = {
        "demo_id": demo_id,
        "blob_set": blob_set,
        "pos_set": int(pos_set) if pos_set else 0,
        "title": title,
        "credit": credit,
    }
    _, status_code = api_post(
        f"/api/blobs/demo_blobs/{demo_id}", method="post", params=settings, files=files
    )
    if status_code != 200:
        return HttpResponse(json.dumps(response), "application/json")
    else:
        return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
# TODO
def ajax_add_blob_template(request):
    blob_set = request.POST["SET"]
    pos_set = request.POST["PositionSet"]
    title = request.POST["Title"]
    credit = request.POST["Credit"]
    template_id = request.POST["TemplateSelection"]
    files = {"blob": request.FILES["Blobs"].file}
    if "VR" in request.FILES:
        files["blob_vr"] = request.FILES["VR"].file

    settings = {
        "blob_set": blob_set,
        "pos_set": int(pos_set) if pos_set else 0,
        "title": title,
        "credit": credit,
    }
    response_api, _ = api_post(
        f"/api/blobs/template_blobs/{template_id}",
        method="post",
        params=settings,
        files=files,
    )
    return HttpResponse(json.dumps(response_api), "application/json")


@login_required(login_url="login")
@never_cache
def detailsBlob(request):
    context = {}
    if "demo_id" in request.GET:  # demo blob edit
        demo_id = request.GET["demo_id"]
        can_edit = user_can_edit_demo(request.user, demo_id)
        set_name = request.GET["set"]
        blob_pos = request.GET["pos"]
        sets, _ = api_post(f"/api/blobs/demo_blobs/{demo_id}", method="get")
        for blobset in sets:
            if blobset["name"] == set_name and blob_pos in blobset["blobs"]:
                blob = blobset["blobs"][blob_pos]
                thumbnail = blob["thumbnail"] if "thumbnail" in blob else ""
                vr = blob["vr"] if "vr" in blob else ""
                context = {
                    "demo_id": request.GET["demo_id"],
                    "pos": blob_pos,
                    "set_name": blobset["name"],
                    "blob_id": blob["id"],
                    "title": blob["title"],
                    "blob": blob["blob"],
                    "format": blob["format"],
                    "credit": blob["credit"],
                    "thumbnail": thumbnail,
                    "vr": vr,
                    "can_edit": can_edit,
                }
                return render(request, "detailsBlob.html", context)

    else:  # Template blob edit
        template_id = request.GET["template_id"]
        template_name = request.GET["template_name"]
        set_name = request.GET["set"]
        blob_pos = request.GET["pos"]
        sets, _ = api_post(f"/api/blobs/templates/{template_id}", method="get")
        for blobset in sets:
            if blobset["name"] == set_name and blob_pos in blobset["blobs"]:
                blob = blobset["blobs"][blob_pos]
                thumbnail = blob["thumbnail"] if "thumbnail" in blob else ""
                vr = blob["vr"] if "vr" in blob else ""
                context = {
                    "template_id": template_id,
                    "template_name": template_name,
                    "pos": blob_pos,
                    "set_name": blobset["name"],
                    "blob_id": blob["id"],
                    "title": blob["title"],
                    "blob": blob["blob"],
                    "format": blob["format"],
                    "credit": blob["credit"],
                    "thumbnail": thumbnail,
                    "vr": vr,
                }
                return render(request, "detailsBlob.html", context)
        return JsonResponse({"status": "OK", "message": "Blob not found"}, status=404)


@login_required(login_url="login")
def ajax_edit_blob_template(request):
    new_blob_set = request.POST["SET"]
    blob_set = request.POST["old_set"]
    new_pos_set = request.POST["PositionSet"]
    pos_set = request.POST["old_pos"]
    title = request.POST["Title"]
    credit = request.POST["Credit"]
    template_id = request.POST["template_id"]
    files = {}
    if "VR" in request.FILES:
        files["vr"] = request.FILES["VR"].file

    response = {}
    settings = {
        "template_id": template_id,
        "blob_set": blob_set,
        "new_blob_set": new_blob_set,
        "pos_set": int(pos_set) if pos_set else 0,
        "new_pos_set": int(new_pos_set) if new_pos_set else 0,
        "title": title,
        "credit": credit,
    }
    _, response_code = api_post(
        f"/api/blobs/template_blobs/{template_id}",
        method="put",
        params=settings,
        files=files,
    )
    if response_code != 204:
        response["status"] = "KO"
        return HttpResponse(json.dumps(response), "application/json")
    else:
        response["status"] = "OK"
        return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
def showDemo(request):
    demo_id = request.GET["demo_id"]
    ddl, ddl_status_code = api_post(f"/api/demoinfo/ddl/{demo_id}", method="get")
    ssh_keys, ssh_response = api_post(f"/api/demoinfo/ssh_keys/{demo_id}", method="get")
    editor_list, _ = api_post(f"/api/demoinfo/demos/{demo_id}/editors", method="get")
    available_editors, _ = api_post(
        f"/api/demoinfo/available_editors/{demo_id}", method="get"
    )
    available_editors = sorted(available_editors, key=lambda e: e["name"])

    if ddl_status_code != 200:
        ddl = "{}"

    if ssh_response != 200:
        pubkey = "(error fetching the ssh public key)"
    else:
        pubkey = ssh_keys["pubkey"]

    can_edit = user_can_edit_demo(request.user, demo_id)

    metainfo_response, _ = api_post(
        f"/api/demoinfo/demo_metainfo/{demo_id}", method="get"
    )
    title = metainfo_response.get("title", "")

    context = {
        "demo_id": demo_id,
        "title": title,
        "ddl": ddl,
        "can_edit": can_edit,
        "editors_list": editor_list,
        "available_editors": available_editors,
        "ssh_pubkey": pubkey,
    }

    return render(request, "showDemo.html", context)


@login_required(login_url="login")
def edit_demo(request):
    old_demo_id = request.POST["demo_id"]
    new_demo_id = request.POST["new_demo_id"]
    title = request.POST["demoTitle"]
    state = request.POST["state"]
    settings = {"demo_id": int(new_demo_id), "title": title, "state": state}

    demoinfo_response, demo_status = api_post(
        f"/api/demoinfo/demo/{old_demo_id}", method="patch", data=settings
    )
    settings = {"new_demo_id": new_demo_id}
    _, blobs_response_code = api_post(
        f"/api/blobs/demos/{old_demo_id}",
        method="put",
        params=settings,
    )
    settings = {"new_demo_id": new_demo_id}
    _, archive_response_code = api_post(
        f"/api/archive/demo/{old_demo_id}?new_demo_id={new_demo_id}", "put"
    )

    response = {}
    if demo_status != 201 or blobs_response_code != 201 or archive_response_code != 204:
        response["status"] = "KO"
        response["message"] = demoinfo_response.get("error")
        return HttpResponse(json.dumps(response), "application/json")
    else:
        return HttpResponseRedirect(f"/cp2/showDemo?demo_id={new_demo_id}")


@login_required(login_url="login")
def ddl_history(request):
    demo_id = request.GET["demo_id"]
    title = request.GET.get("title", "")

    ddl_history, _ = api_post(f"/api/demoinfo/ddl_history/{demo_id}", method="get")

    context = {
        "demo_id": demo_id,
        "title": title,
        "ddl_history": ddl_history,
    }
    return render(request, "ddl_history.html", context)


@login_required(login_url="login")
def ajax_user_can_edit_demo(request):
    demo_id = request.POST["demoID"]
    if user_can_edit_demo(request.user, demo_id):
        return HttpResponse(json.dumps({"can_edit": True}), "application/json")
    else:
        return HttpResponse(json.dumps({"can_edit": False}), "application/json")


@login_required(login_url="login")
def ajax_remove_vr(request):
    blob_id = request.POST["blob_id"]
    _, response_code = api_post(
        f"/api/blobs/visual_representations/{blob_id}", method="delete"
    )
    if response_code != 204:
        return JsonResponse({"message": "Could not remove VR"}, status=404)
    else:
        return JsonResponse({"status": "OK"}, status=200)


@login_required(login_url="login")
def ajax_show_DDL(request):
    demo_id = request.POST["demo_id"]
    response = {}
    response, _ = api_post(f"/api/demoinfo/ddl/{demo_id}", method="get")
    return HttpResponse(json.dumps(response), "application/json")


@login_required(login_url="login")
def ajax_save_DDL(request):
    demo_id = request.POST["demo_id"]
    ddl = request.POST["ddl"]

    if user_can_edit_demo(request.user, demo_id):
        api_post(
            f"/api/demoinfo/ddl/{demo_id}",
            method="post",
            json=json.loads(ddl),
        )
        return JsonResponse({"status": "OK"}, status=200)
    else:
        return JsonResponse({"status": "OK", "message": "Unauthorized"}, status=401)


@login_required(login_url="login")
def showBlobsDemo(request):
    demo_id = request.GET["demo_id"]
    can_edit = user_can_edit_demo(request.user, demo_id)
    blob_sets, _ = api_post(f"/api/blobs/demo_owned_blobs/{demo_id}", method="get")

    demo_used_templates, _ = api_post(
        f"/api/blobs/demo_templates/{demo_id}", method="get"
    )

    template_list, _ = api_post("/api/blobs/templates", "get")

    context = {
        "can_edit": can_edit,
        "demo_id": demo_id,
        "blob_sets": blob_sets,
        "demo_used_templates": demo_used_templates,
        "template_list": template_list,
    }

    return render(request, "showBlobsDemo.html", context)


def get_demo_extras_info(demo_id: int) -> dict:
    response, _ = api_post(f"/api/demoinfo/demoextras/{demo_id}", method="get")
    size = response.get("size")
    extras_url = response.get("url")

    extras_name = None
    if extras_url:
        extras_name = response["url"].split("/")[-1]
        extras_name = urllib.parse.unquote(extras_name)

    date = None
    if "date" in response:
        timestamp = response["date"]
        date = datetime.fromtimestamp(timestamp)

    info = {
        "demo_id": demo_id,
        "extras_url": extras_url,
        "extras_name": extras_name,
        "date": date,
        "size": size,
    }
    return info


@login_required(login_url="login")
def demoExtras(request):
    demo_id = request.GET["demo_id"]
    info = get_demo_extras_info(int(demo_id))

    context = {
        "demo_id": demo_id,
        "can_edit": user_can_edit_demo(request.user, demo_id),
        **info,
    }
    return render(request, "demoExtras.html", context)


@login_required(login_url="login")
@csrf_protect
def ajax_add_demo_extras(request):
    demo_id = request.POST["demo_id"]
    file = request.FILES["demoextras"]
    filename = request.FILES["demoextras"].name

    context = {
        "demo_id": demo_id,
        "can_edit": user_can_edit_demo(request.user, demo_id),
    }

    if user_can_edit_demo(request.user, demo_id):
        params = {"demoextras_name": filename}
        files = {"demoextras": file}
        response, status = api_post(
            f"/api/demoinfo/demoextras/{demo_id}",
            method="post",
            data=params,
            files=files,
        )
        if status != 201:
            context["error"] = response.get("detail", "Could not add the demoextras")
            return render(request, "demoExtras.html", context, status=500)

    info = get_demo_extras_info(int(demo_id))
    context.update(**info)

    return render(request, "demoExtras.html", context, status=200)


@login_required(login_url="login")
def ajax_delete_demo_extras(request):
    demo_id = request.GET["demo_id"]
    if user_can_edit_demo(request.user, demo_id):
        _, status_code = api_post(
            f"/api/demoinfo/demoextras/{demo_id}", method="delete"
        )
        if status_code != 204:
            message = "Error while removing demoextras"
            return render(
                request, "error.html", {"error_code": 404, "message": message}
            )
    return HttpResponseRedirect(f"/cp2/demoExtras?demo_id={demo_id}")


@login_required(login_url="login")
def ajax_add_template_to_demo(request):
    demo_id = request.POST["demo_id"]
    template_id = request.POST["template_id"]
    settings = {"demo_id": demo_id, "template_id": template_id}
    response = {}
    if user_can_edit_demo(request.user, demo_id):
        _, response_code = api_post(
            f"/api/blobs/add_template_to_demo/{demo_id}", method="post", params=settings
        )
        if response_code != 201:
            response["status"] = "KO"
            return HttpResponse(json.dumps(response), "application/json")
        else:
            response["status"] = "OK"
            return HttpResponse(json.dumps(response), "application/json")
    else:
        return render(request, "homepage.html")


@login_required(login_url="login")
def ajax_remove_template_to_demo(request):
    demo_id = request.POST["demo_id"]
    template_id = request.POST["template_id"]
    settings = {"demo_id": demo_id, "template_id": template_id}
    if user_can_edit_demo(request.user, demo_id):
        _, status_code = api_post(
            f"/api/blobs/demo_templates/{demo_id}", method="delete", params=settings
        )
        return JsonResponse({}, status=status_code)
    else:
        return render(request, "homepage.html")


@login_required(login_url="login")
def ajax_edit_blob_demo(request):
    demo_id = request.POST["demo_id"]
    files = {}
    if "VR" in request.FILES:
        files["vr"] = request.FILES["VR"].file
    if user_can_edit_demo(request.user, demo_id):
        settings = {
            "demo_id": demo_id,
            "blob_set": request.POST["old_set"],
            "new_blob_set": request.POST["SET"],
            "pos_set": request.POST["old_pos"],
            "new_pos_set": request.POST["PositionSet"],
            "title": request.POST["Title"],
            "credit": request.POST["Credit"],
        }
        _, response_code = api_post(
            f"/api/blobs/demo_blobs/{demo_id}",
            method="put",
            params=settings,
            files=files,
        )

        if response_code != 204:
            return JsonResponse({"status": "KO"}, status=200)
        else:
            return JsonResponse({"status": "OK"}, status=200)
    else:
        return render(request, "homepage.html")


@login_required(login_url="login")
def show_archive(request):
    demo_id = request.GET["demo_id"]
    title = request.GET.get("title", "")

    if "page" in request.GET:
        page = request.GET["page"]
    else:
        page = 1

    archive_response, _ = api_post(
        f"/api/archive/page/{page}?demo_id={demo_id}", method="get"
    )
    experiments = archive_response["experiments"]
    meta = archive_response["meta_info"]

    context = {
        "title": title,
        "demo_id": demo_id,
        "experiments": experiments,
        "meta": meta,
        "page": int(page),
        "can_edit": user_can_edit_demo(request.user, demo_id),
    }
    return render(request, "archive.html", context)


@login_required(login_url="login")
def show_experiment(request):
    demo_id = request.GET["demo_id"]

    if "experiment_id" in request.GET:
        experiment_id = request.GET["experiment_id"]
        archive_response, status_code = api_post(
            f"/api/archive/experiment/{experiment_id}", "get"
        )
        if status_code == 200:
            experiment = archive_response
        else:
            message = "Experiment not found"
            return render(
                request, "error.html", {"error_code": 404, "message": message}
            )

    context = {
        "demo_id": demo_id,
        "experiment": experiment,
        "can_edit": user_can_edit_demo(request.user, demo_id),
    }
    return render(request, "showExperiment.html", context)


@login_required(login_url="login")
def ajax_delete_experiment(request):
    demo_id = request.POST["demo_id"]
    experiment_id = request.POST["experiment_id"]
    if user_can_edit_demo(request.user, demo_id):
        _, status_code = api_post(f"/api/archive/experiment/{experiment_id}", "delete")

        if status_code != 204:
            return HttpResponse(json.dumps({"status": "KO"}), "application/json")
        else:
            return HttpResponse(json.dumps({"status": "OK"}), "application/json")
