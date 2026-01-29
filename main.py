from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        run.logger.info('The stream has been activated.')  # заглушка
        run.create_wrapped_threads()
        run.logger.info('The stream has been deactivated.')  # заглушка
    except Exception as e:
        print(f'The check returned an error: {e} Press Enter to finish.')


if __name__ == '__main__':
    main()
