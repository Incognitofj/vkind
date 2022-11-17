from community import Community

def main():
    community_token = ""
    user_token =""
    # Запуск процесса
    comm = Community(community_token, user_token)
    comm.listen()


if __name__ == "__main__":
    main()
