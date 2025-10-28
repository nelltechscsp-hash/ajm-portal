#!/bin/bash
# Script: auto_commit_push.sh
# Uso: ./auto_commit_push.sh "Mensaje de commit"

cd /opt/odoo/custom_addons

git add .
git status --porcelain | grep . && {
    git commit -m "$1"
    git push origin master
} || {
    echo "No hay cambios para subir."
}
