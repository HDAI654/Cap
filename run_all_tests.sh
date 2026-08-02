#!/bin/sh

print_green_banner() {
    text="$1"
    width=$(tput cols 2>/dev/null || echo 80) 
    green="\033[32m"
    reset="\033[0m"

    if [ -z "$text" ]; then
        printf "${green}%${width}s${reset}\n" | tr ' ' '='
    else
        text_length=${#text}
        side_length=$(( (width - text_length - 2) / 2 ))
        [ $side_length -lt 0 ] && side_length=0
        left=$(printf "%${side_length}s" | tr ' ' '=')
        right=$(printf "%${side_length}s" | tr ' ' '=')
        [ $(( (width - text_length - 2) % 2 )) -ne 0 ] && right="${right}="
        printf "${green}%s %s %s${reset}\n" "$left" "$text" "$right"
    fi
}

print_green_banner "Running wallet_service tests"
sh run_tests.sh wallet_service test/
print_green_banner "wallet_service tests finished successfully"
print_green_banner "" 

print_green_banner "Running order_service tests"
sh run_tests.sh order_service test/
print_green_banner "order_service tests finished successfully"
print_green_banner ""

print_green_banner "Running matching_engine tests"
sh run_tests.sh matching_engine test/
print_green_banner "matching_engine tests finished successfully"
print_green_banner ""

print_green_banner "Running admin_service tests"
sh run_tests.sh admin_service test/
print_green_banner "admin_service tests finished successfully"
print_green_banner ""

print_green_banner "Running market_data_service tests"
sh run_tests.sh market_data_service test/
print_green_banner "market_data_service tests finished successfully"
print_green_banner ""