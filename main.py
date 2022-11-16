from community import Community

def main():
    # Токен сообщества (Права messages, photos и docs)
    community_token = ""
    # Токен пользователя (от имени сообщества нельзя искать людей)
    user_token = ""
    # Запуск процесса
    comm = Community(community_token, user_token)
    comm.listen()


if __name__ == "__main__":
    main()
