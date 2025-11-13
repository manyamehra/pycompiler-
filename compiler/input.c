{int sumArray(int size) {
        int arr[10];
        int sum;
        int i;
        sum = 0;
        for(i = 0; i < size; i = i + 1) {
            arr[i] = i;
            sum = sum + arr[i];
        }
        return sum;
    }}
